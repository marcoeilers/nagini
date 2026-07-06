"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""
Transport-agnostic verification service.

Wraps the long-lived process state (JVM, parsed Silver resources, and the
in-process ViperServer) behind a small API that returns *structured* results
instead of printing strings. This is the shared core that the LSP and MCP
servers build on; it can also be reused by the existing ZMQ server.
"""


import argparse
import ast
import logging
import os
import threading
import time

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from nagini_translation.lib import config
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.typeinfo import TypeException
from nagini_translation.lib.util import (
    ConsistencyException,
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.main import (
    load_sil_files,
    translate,
    TYPE_ERROR_MATCHER,
    verify as verify_program,
)
from nagini_translation.verifier import Failure, Success, ViperVerifier


@dataclass
class Diagnostic:
    """
    A single structured verification/translation diagnostic.

    Positions use Nagini's native convention: ``line`` is 1-indexed and
    ``col`` is 0-indexed. LSP adapters must convert to 0-indexed lines
    (``line - 1``); the existing ``ide_mode`` format instead renders columns
    1-indexed (``col + 1``), so don't mix the two conventions.
    """
    file: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    message: str
    code: str
    severity: str = 'error'
    source: str = 'nagini'
    reason: Optional[str] = None
    reason_position: Optional[Tuple[int, int]] = None
    vias: List[Tuple[str, str]] = field(default_factory=list)
    counterexample: Optional[str] = None
    branch_conditions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'file': self.file,
            'startLine': self.start_line,
            'startCol': self.start_col,
            'endLine': self.end_line,
            'endCol': self.end_col,
            'severity': self.severity,
            'code': self.code,
            'source': self.source,
            'message': self.message,
            'reason': self.reason,
            'reasonPosition': self.reason_position,
            'vias': self.vias,
            'counterexample': self.counterexample,
            'branchConditions': self.branch_conditions,
        }


@dataclass
class VerifyResult:
    success: bool
    diagnostics: List[Diagnostic]
    duration: float
    translation_failed: bool = False
    cancelled: bool = False

    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'translationFailed': self.translation_failed,
            'cancelled': self.cancelled,
            'duration': self.duration,
            'diagnostics': [d.to_dict() for d in self.diagnostics],
        }


class VerificationService:
    """
    Long-lived, in-process Nagini verification service.

    A single instance owns one JVM and (optionally) one ViperServer, preloads
    the Silver resources once, and serializes verification requests. Because
    translation relies on global state (``error_manager`` is cleared per
    ``translate`` call, and the parsed ``sil_programs`` is a module global),
    only one verification may run at a time; :meth:`cancel` preempts a running
    one without taking the lock.
    """

    def __init__(self, *, z3_path: str = None, viper_jar_path: str = None,
                 boogie_path: str = None, mypy_path: str = None,
                 int_bitops_size: int = 8, use_viper_server: bool = True,
                 verifier_backend: str = 'silicon', sif=False,
                 float_encoding: str = None,
                 disable_branch_conditions: bool = False):
        if viper_jar_path:
            config.classpath = viper_jar_path
        if z3_path:
            config.z3_path = z3_path
        if boogie_path:
            config.boogie_path = boogie_path
        if mypy_path:
            config.mypy_path = mypy_path
        config.set_verifier(verifier_backend)
        if use_viper_server:
            config.enable_viper_server(verifier_backend)
        if not config.classpath:
            raise ValueError('No Viper jar path configured (set viper_jar_path '
                             'or the VIPERJAVAPATH environment variable).')
        if not config.z3_path:
            raise ValueError('No Z3 path configured (set z3_path or the Z3_EXE '
                             'environment variable).')

        self._backend = verifier_backend
        self._sif = sif
        self._float_encoding = float_encoding
        self._bv_size = int_bitops_size
        self._disable_branch_conditions = disable_branch_conditions
        # The obligation encoding is auto-detected per program by translate(),
        # which persistently sets obligation_config.disable_all once a program
        # without obligations is seen. In a long-lived service that would then
        # break a later program that *does* use obligations, so we snapshot the
        # initial setting and restore it before every verification.
        self._initial_obligations_disable_all = config.obligation_config.disable_all
        # Guards all access to the global error_manager state (translation and
        # error conversion). The slow Viper verification runs *outside* this
        # lock, so multiple verifications proceed concurrently.
        self._state_lock = threading.Lock()
        # Maps a caller-chosen token to the in-flight VerJobId, for precise
        # per-job cancellation.
        self._jobs = {}
        self._jobs_lock = threading.Lock()

        self.jvm = JVM(config.classpath)
        # The JVM (logback/Silicon/ViperServer) writes to stdout, which would
        # corrupt the JSON-RPC stream of a stdio-based LSP/MCP frontend. Route
        # all JVM stdout to stderr; we never rely on JVM stdout.
        try:
            self.jvm.java.lang.System.setOut(self.jvm.java.lang.System.err)
        except Exception:
            logging.exception('Could not redirect JVM stdout.')
        # Preload the Silver resources once (sets the main module's global so
        # translate() reuses it). Tied to the service-level sif/float/bv_size.
        import nagini_translation.main as main_module
        main_module.sil_programs = load_sil_files(self.jvm, int_bitops_size, sif,
                                                  float_encoding)
        if config.use_viper_server:
            try:
                from nagini_translation.viper_server import get_viper_server_manager
                get_viper_server_manager(self.jvm).start()
            except Exception:
                logging.exception('ViperServer could not be started; verification '
                                  'will use the direct Silicon backend.')

    # -- public API ---------------------------------------------------------

    def verify(self, path: str, *, selected: Set[str] = None, base_dir: str = None,
               arp: bool = False, counterexample: bool = False,
               ignore_global: bool = False,
               job_token: str = None) -> VerifyResult:
        """Translate and verify the file at ``path`` and return structured results.

        Multiple calls may run concurrently: translation is serialized but the
        Viper verification overlaps. Pass a ``job_token`` to allow precise
        cancellation of this request via :meth:`cancel`. Set ``ignore_global``
        to skip verification of top-level (module-global) statements.
        """
        path = os.path.abspath(path)
        if self._can_run_concurrently(arp):
            return self._verify_concurrent(path, selected, base_dir, counterexample,
                                           ignore_global, job_token)
        with self._state_lock:
            return self._verify_serial(path, selected, base_dir, arp, counterexample,
                                       ignore_global)

    def _reset_obligations(self) -> None:
        """Restore the obligation auto-detection setting before a translation.

        Must be called while holding the state lock. Setting ``disable_all`` to
        ``None`` would be written as the string ``"None"`` (breaking getboolean),
        so we remove the key to return to auto-detection instead.
        """
        section = config.obligation_config._info
        if self._initial_obligations_disable_all is None:
            if 'disable_all' in section:
                del section['disable_all']
        else:
            config.obligation_config.disable_all = self._initial_obligations_disable_all

    def cancel(self, job_token: str = None) -> None:
        """Cancel a verification.

        With a ``job_token`` that is currently running, stops precisely that
        job; without one, interrupts all running jobs. Does not take the state
        lock, so it can preempt an in-flight verification.
        """
        if not config.use_viper_server:
            return
        try:
            from nagini_translation.viper_server import get_viper_server_manager
            manager = get_viper_server_manager(self.jvm)
            if job_token is not None:
                with self._jobs_lock:
                    job_id = self._jobs.get(job_token)
                if job_id is not None:
                    manager.cancel_job(job_id)
            else:
                manager.cancel_all()
        except Exception:
            logging.exception('Error cancelling verification.')

    def _can_run_concurrently(self, arp: bool) -> bool:
        if (arp or self._sif or self._backend not in ('silicon', 'carbon')
                or not config.use_viper_server):
            return False
        try:
            from nagini_translation.viper_server import get_viper_server_manager
            return get_viper_server_manager(self.jvm).started
        except Exception:
            return False

    def flush_cache(self) -> None:
        if config.use_viper_server:
            try:
                from nagini_translation.viper_server import get_viper_server_manager
                get_viper_server_manager(self.jvm).flush_cache()
            except Exception:
                logging.exception('Error flushing ViperServer cache.')

    def shutdown(self) -> None:
        if config.use_viper_server:
            try:
                from nagini_translation.viper_server import get_viper_server_manager
                get_viper_server_manager(self.jvm).stop()
            except Exception:
                logging.exception('Error shutting down ViperServer.')

    def current_options(self) -> dict:
        """The effective configuration, as client-facing (camelCase) options."""
        return {
            'verifier': self._backend,
            'sif': self._sif,
            'intBitopsSize': self._bv_size,
            'floatEncoding': self._float_encoding,
            'useViperServer': config.use_viper_server,
            'disableBranchConditions': self._disable_branch_conditions,
            'z3Path': config.z3_path,
            'boogiePath': config.boogie_path,
            'mypyPath': config.mypy_path,
        }

    def reconfigure(self, **options) -> dict:
        """Change options between verification requests; return the effective
        configuration.

        Takes the same (snake_case) keys as the constructor. Options that
        determine the JVM classpath (``viper_jar_path``) cannot change once the
        JVM has started and are ignored. Options that affect the parsed Silver
        resources (``sif``, ``int_bitops_size``, ``float_encoding``) trigger a
        reload of those resources. Serialized against in-flight translations via
        the state lock; already-submitted verifications are unaffected.
        """
        with self._state_lock:
            if options.get('viper_jar_path'):
                logging.warning('viper_jar_path cannot be changed at runtime; '
                                'ignoring.')
            if options.get('z3_path') is not None:
                config.z3_path = options['z3_path']
            if options.get('boogie_path') is not None:
                config.boogie_path = options['boogie_path']
            if options.get('mypy_path') is not None:
                config.mypy_path = options['mypy_path']
            if options.get('verifier_backend') is not None:
                self._backend = options['verifier_backend']
            if options.get('use_viper_server') is not None:
                config.use_viper_server = bool(options['use_viper_server'])
            if options.get('disable_branch_conditions') is not None:
                self._disable_branch_conditions = bool(
                    options['disable_branch_conditions'])
            reload_needed = False
            if options.get('sif') is not None and options['sif'] != self._sif:
                self._sif = options['sif']
                reload_needed = True
            if (options.get('int_bitops_size') is not None
                    and options['int_bitops_size'] != self._bv_size):
                self._bv_size = options['int_bitops_size']
                reload_needed = True
            if ('float_encoding' in options
                    and options['float_encoding'] != self._float_encoding):
                self._float_encoding = options['float_encoding']
                reload_needed = True
            if reload_needed:
                import nagini_translation.main as main_module
                main_module.sil_programs = load_sil_files(
                    self.jvm, self._bv_size, self._sif, self._float_encoding)
        return self.current_options()

    # -- internals ----------------------------------------------------------

    def _verify_concurrent(self, path, selected, base_dir, counterexample,
                           ignore_global, job_token) -> VerifyResult:
        from nagini_translation.viper_server import (build_carbon_backend_args,
                                                     build_silicon_backend_args,
                                                     get_viper_server_manager)
        manager = get_viper_server_manager(self.jvm)
        start = time.time()
        # 1. Translate and snapshot this job's error-mapping state (serialized).
        with self._state_lock:
            self._reset_obligations()
            try:
                translated = translate(
                    path, self.jvm, self._bv_size,
                    selected=set(selected) if selected else set(), sif=False,
                    base_dir=base_dir, arp=False, counterexample=counterexample,
                    ignore_global=ignore_global, float_encoding=self._float_encoding)
            except (TypeException, InvalidProgramException, UnsupportedException) as e:
                return VerifyResult(False, self._exception_diagnostics(e, path),
                                    time.time() - start, translation_failed=True)
            except ConsistencyException as e:
                return VerifyResult(False, [self._point_diagnostic(
                    path, e.message + ': Translated AST contains inconsistencies.',
                    'consistency.error')], time.time() - start,
                    translation_failed=True)
            if translated is None:
                return VerifyResult(False, [self._point_diagnostic(
                    path, 'Type checking failed.', 'type.error')],
                    time.time() - start, translation_failed=True)
            modules, prog = translated
            snapshot = (dict(error_manager._items),
                        dict(error_manager._conversion_rules))
            error_manager.clear()

        # 2. Submit and await the result lock-free, so jobs overlap in Viper.
        if self._backend == 'carbon':
            backend_args = build_carbon_backend_args([])
        else:
            backend_args = build_silicon_backend_args(
                [], counterexample, self._disable_branch_conditions)
        job_id = manager.submit(prog, path, backend_args, backend=self._backend)
        if job_token is not None:
            with self._jobs_lock:
                self._jobs[job_token] = job_id
        try:
            result = manager.await_result(job_id)
        except Exception:
            # Most commonly this is a cancelled job (its actor was stopped).
            logging.debug('Verification job failed or was cancelled.', exc_info=True)
            return VerifyResult(False, [], time.time() - start, cancelled=True)
        finally:
            if job_token is not None:
                with self._jobs_lock:
                    # Only remove our own mapping; a newer run may have already
                    # reused this token (e.g. an editor re-saving the same file).
                    if self._jobs.get(job_token) is job_id:
                        del self._jobs[job_token]

        duration = time.time() - start
        if result is None:
            return VerifyResult(False, [self._point_diagnostic(
                path, 'Internal verifier error (see server log).',
                'verifier.error')], duration)

        # 3. Convert the result with this job's snapshot installed (serialized).
        is_failure = isinstance(result, self.jvm.viper.silver.verifier.Failure)
        if not is_failure:
            return VerifyResult(True, [], duration)
        with self._state_lock:
            error_manager._items, error_manager._conversion_rules = snapshot
            try:
                it = result.errors().toIterator()
                errors = []
                while it.hasNext():
                    errors.append(it.next())
                failure = Failure(errors, self.jvm, modules, self._sif)
                diagnostics = self._failure_diagnostics(failure, path)
            finally:
                error_manager.clear()
        return VerifyResult(False, diagnostics, duration)

    def _verify_serial(self, path, selected, base_dir, arp,
                       counterexample, ignore_global) -> VerifyResult:
        start = time.time()
        try:
            self._reset_obligations()
            selected_set = set(selected) if selected else set()
            translated = translate(
                path, self.jvm, self._bv_size, selected=selected_set,
                sif=self._sif, base_dir=base_dir, arp=arp,
                counterexample=counterexample, ignore_global=ignore_global,
                float_encoding=self._float_encoding)
            if translated is None:
                return VerifyResult(False, [self._point_diagnostic(
                    path, 'Type checking failed.', 'type.error')],
                    time.time() - start, translation_failed=True)
            modules, prog = translated
            backend = (ViperVerifier.silicon if self._backend == 'silicon'
                       else ViperVerifier.carbon)
            vresult = verify_program(
                modules, prog, path, self.jvm, [], backend=backend, arp=arp,
                counterexample=counterexample, sif=self._sif,
                disable_branch_conditions=self._disable_branch_conditions)
            duration = time.time() - start
            if vresult is None:
                # main.verify swallows JVM exceptions and returns None.
                return VerifyResult(False, [self._point_diagnostic(
                    path, 'Internal verifier error (see server log).',
                    'verifier.error')], duration)
            if isinstance(vresult, Failure):
                return VerifyResult(False, self._failure_diagnostics(vresult, path),
                                    duration)
            return VerifyResult(True, [], duration)
        except (TypeException, InvalidProgramException, UnsupportedException) as e:
            return VerifyResult(False, self._exception_diagnostics(e, path),
                                time.time() - start, translation_failed=True)
        except ConsistencyException as e:
            return VerifyResult(False, [self._point_diagnostic(
                path, e.message + ': Translated AST contains inconsistencies.',
                'consistency.error')], time.time() - start, translation_failed=True)

    def _failure_diagnostics(self, failure: Failure, path: str) -> List[Diagnostic]:
        diagnostics = []
        seen = set()
        for error in failure.errors:
            pos = error.position
            try:
                file_name = pos.file_name
            except Exception:
                file_name = path
            vias = [(str(reason), str(p))
                    for reason, p in (error.reason.vias or error._vias or [])]
            try:
                reason_pos = (error.reason.position.line, error.reason.position.column)
            except Exception:
                reason_pos = None
            diag = Diagnostic(
                file=file_name,
                start_line=pos.line, start_col=pos.column,
                end_line=pos.line_end, end_col=pos.column_end,
                message=error.message,
                code=error.full_id,
                reason=error.reason.string(False),
                reason_position=reason_pos,
                vias=vias,
                counterexample=(str(error._inputs)
                                if error._inputs is not None else None),
                branch_conditions=list(error.bcs) if error.bcs else [],
            )
            key = (diag.file, diag.start_line, diag.start_col, diag.code, diag.message)
            if key not in seen:
                seen.add(key)
                diagnostics.append(diag)
        return diagnostics

    def _exception_diagnostics(self, e, path: str) -> List[Diagnostic]:
        if isinstance(e, (InvalidProgramException, UnsupportedException)):
            if isinstance(e, InvalidProgramException):
                code = 'invalid.program'
                message = 'Invalid program: ' + (e.message or e.code)
            else:
                code = 'unsupported'
                detail = e.args[0] if e.args and e.args[0] else ast.unparse(e.node)
                message = 'Not supported: ' + detail
            line = getattr(e.node, 'lineno', 1)
            col = getattr(e.node, 'col_offset', 0)
            return [Diagnostic(file=path, start_line=line, start_col=col,
                               end_line=line, end_col=col, message=message,
                               code=code)]
        # TypeException
        diagnostics = []
        for msg in e.messages:
            parts = TYPE_ERROR_MATCHER.match(msg)
            if parts:
                parts = parts.groupdict()
                file = parts['file']
                if file == '__main__':
                    file = path
                line = int(parts['line'])
                diagnostics.append(Diagnostic(
                    file=file, start_line=line, start_col=0, end_line=line,
                    end_col=0, message='Type error: ' + parts['msg'],
                    code='type.error'))
            else:
                diagnostics.append(self._point_diagnostic(path, msg, 'type.error'))
        return diagnostics

    @staticmethod
    def _point_diagnostic(path: str, message: str, code: str) -> Diagnostic:
        return Diagnostic(file=path, start_line=1, start_col=0, end_line=1,
                          end_col=0, message=message, code=code)


# Maps client-facing (camelCase) option keys to VerificationService kwargs.
# Shared by the LSP (initializationOptions) and MCP (configure) frontends.
OPTION_TO_KWARG = {
    'z3Path': 'z3_path',
    'viperJarPath': 'viper_jar_path',
    'boogiePath': 'boogie_path',
    'mypyPath': 'mypy_path',
    'verifier': 'verifier_backend',
    'sif': 'sif',
    'intBitopsSize': 'int_bitops_size',
    'floatEncoding': 'float_encoding',
    'useViperServer': 'use_viper_server',
    'disableBranchConditions': 'disable_branch_conditions',
}


def options_to_kwargs(options) -> dict:
    """Translate client-facing (camelCase) option keys to service kwargs.

    Unknown keys and keys with a null value are ignored. Accepts a dict or None.
    """
    kwargs = {}
    if not options:
        return kwargs
    if not isinstance(options, dict):
        options = getattr(options, '__dict__', None) or {}
    for option_key, kwarg in OPTION_TO_KWARG.items():
        if options.get(option_key) is not None:
            kwargs[kwarg] = options[option_key]
    return kwargs


def add_service_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Add the CLI arguments needed to construct a :class:`VerificationService`."""
    parser.add_argument('--viper-jar-path', default=config.classpath,
                        help='Java classpath for Viper/ViperServer')
    parser.add_argument('--z3', default=config.z3_path, help='path to the Z3 executable')
    parser.add_argument('--boogie', default=config.boogie_path,
                        help='path to the Boogie executable (Carbon only)')
    parser.add_argument('--mypy-path', default=config.mypy_path)
    parser.add_argument('--verifier', default='silicon', choices=('silicon', 'carbon'))
    parser.add_argument('--sif', default=False)
    parser.add_argument('--int-bitops-size', type=int, default=8)
    parser.add_argument('--float-encoding', default=None)
    parser.add_argument('--disable-branch-conditions', action='store_true',
                        help='do not report branch conditions for verification '
                             'errors (Silicon backend)')
    parser.add_argument('--no-viper-server', action='store_true',
                        help='disable the in-process ViperServer backend')
    return parser


def service_kwargs_from_args(args: argparse.Namespace) -> dict:
    """The :class:`VerificationService` constructor kwargs from parsed CLI args.

    Returned as a plain dict so frontends (e.g. the LSP server) can override
    individual entries with client-provided ``initializationOptions`` before
    constructing the service.
    """
    return dict(
        z3_path=args.z3, viper_jar_path=args.viper_jar_path, boogie_path=args.boogie,
        mypy_path=args.mypy_path, int_bitops_size=args.int_bitops_size,
        use_viper_server=not args.no_viper_server, verifier_backend=args.verifier,
        sif=args.sif, float_encoding=args.float_encoding,
        disable_branch_conditions=args.disable_branch_conditions)


def make_service(args: argparse.Namespace) -> VerificationService:
    """Build a :class:`VerificationService` from parsed CLI arguments."""
    return VerificationService(**service_kwargs_from_args(args))
