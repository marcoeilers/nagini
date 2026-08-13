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
import glob
import hashlib
import json
import logging
import os
import re
import signal
import threading
import time

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from nagini_translation.lib import config
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.errors.messages import invalid_program_message
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
    debug: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {
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
        if self.debug is not None:
            result['debug'] = self.debug
        return result


@dataclass
class VerifyResult:
    success: bool
    diagnostics: List[Diagnostic]
    duration: float
    translation_failed: bool = False
    cancelled: bool = False
    viper_program: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            'success': self.success,
            'translationFailed': self.translation_failed,
            'cancelled': self.cancelled,
            'duration': self.duration,
            'diagnostics': [d.to_dict() for d in self.diagnostics],
        }
        if self.viper_program is not None:
            result['viperProgram'] = self.viper_program
        return result


def _scala_strings(collection) -> List[str]:
    """Stringify the elements of any Scala collection via its iterator."""
    out = []
    iterator = (collection.toIterator() if hasattr(collection, 'toIterator')
                else collection.iterator())
    while iterator.hasNext():
        out.append(str(iterator.next()))
    return out


def _heap_chunks(heap) -> object:
    """Render a Silicon heap as its chunk list. ``str(heap)`` is just the Java
    object identity (``ListBackedHeap@6798e882``) — every agent run confirmed it
    carries zero information — while the chunks themselves print as
    ``resource(receiver; snapshot, permission)``. Falls back to the raw string
    on any API surprise."""
    try:
        return _scala_strings(heap.values())
    except Exception:
        return str(heap)


def _old_heaps(old_heaps) -> object:
    """Render Silicon's label -> heap map with the same chunk treatment."""
    try:
        out = {}
        it = old_heaps.iterator()
        while it.hasNext():
            kv = it.next()
            out[str(kv._1())] = _heap_chunks(kv._2())
        return out
    except Exception:
        return str(old_heaps)


_SYM_SUFFIX = re.compile(r'@\d+@\d+')
_CHECK_DEFINED = re.compile(r'_checkDefined\(_,\s*([^,()]+),\s*\d+\)')


def _pretty_term(term: str) -> str:
    """Best-effort readable rendering of a Silicon term string: strip the
    ``@line@col`` freshness suffixes (``b@13@07`` -> ``b``, matching the
    Python-level name the store maps it from) and unwrap ``_checkDefined``
    shims. The raw term is always preserved alongside — this is a reading
    aid, not a replacement."""
    term = _SYM_SUFFIX.sub('', term)
    for _ in range(8):
        unwrapped = _CHECK_DEFINED.sub(r'\1', term)
        if unwrapped == term:
            break
        term = unwrapped
    return term


def _debug_payload(error) -> Optional[dict]:
    """Project Silicon's SMT state failure context into a JSON-friendly dict.

    Attached only when Silicon recorded the symbolic state (its
    ``--smtStateOnError`` option, passed through ``viper_args``); returns
    ``None`` otherwise. Everything is stringified eagerly here — the live
    ``state`` object itself cannot leave the JVM, so the store/heap
    projections stand in for it.
    """
    try:
        jvm_error = getattr(error, '_error', None)
        if jvm_error is None or not hasattr(jvm_error, 'failureContexts'):
            return None
        contexts = jvm_error.failureContexts()
        if not contexts.nonEmpty():
            return None
        ctx = contexts.head()
        if not hasattr(ctx, 'proverEmits'):
            return None  # plain SiliconFailureContext, no SMT state
        payload = {
            'failedAssertion': str(ctx.failedAssertion()),
            'failedAssertionPretty': _pretty_term(str(ctx.failedAssertion())),
            'assumptions': _scala_strings(ctx.assumptions()),
            'preambleAssumptions': _scala_strings(ctx.preambleAssumptions()),
            'macroDecls': _scala_strings(ctx.macroDecls()),
            'functionDecls': _scala_strings(ctx.functionDecls()),
            'proverEmits': _scala_strings(ctx.proverEmits()),
            'branchConditions': _scala_strings(ctx.branchConditions()),
        }
        if ctx.reasonUnknown().isDefined():
            payload['reasonUnknown'] = str(ctx.reasonUnknown().get())
        if ctx.rlimitDelta().isDefined():
            # Z3 rlimit units spent on the failing check itself; the unit
            # assertTimeout budgets are enforced in (ms * z3ResourcesPerMillisecond).
            payload['rlimitDelta'] = int(str(ctx.rlimitDelta().get()))
        if ctx.state().isDefined():
            state = ctx.state().get()
            payload['state'] = {
                'store': str(state.g().termValues()),
                'heap': _heap_chunks(state.h()),
                'oldHeaps': _old_heaps(state.oldHeaps()),
            }
        return payload
    except Exception:
        logging.exception('Failed to project the SMT state failure context.')
        return None


# Grace period on top of the backend's own --timeout before the service declares a
# verification wedged and force-kills its prover processes (see _hard_wall_seconds).
HARD_DEADLINE_GRACE = 60


def _hard_wall_seconds(backend_args) -> Optional[int]:
    """Wall cap for one verification job, derived from the effective backend args.

    Silicon's --timeout produces a TimeoutOccurred *result* at T seconds, but the
    result is only delivered after teardown joins the worker pool — and a prover
    stuck deep in a single hard query ignores the JVM-side interrupt, so the job
    (and, since jobs serialize per client, every queued call behind it) can grind
    for many extra minutes. Cap the wait at T plus a grace period; None (no
    --timeout, or --timeout=0) means wait indefinitely.
    """
    timeout = None
    args = list(backend_args)
    for i, arg in enumerate(args):
        if arg.startswith('--timeout='):
            timeout = arg.split('=', 1)[1]
        elif arg == '--timeout' and i + 1 < len(args):
            timeout = args[i + 1]
    try:
        seconds = int(timeout)
    except (TypeError, ValueError):
        return None
    return seconds + HARD_DEADLINE_GRACE if seconds > 0 else None


def _is_await_timeout(exc: Exception) -> bool:
    """True for the TimeoutException scala.concurrent.Await.result raises."""
    return ('TimeoutException' in type(exc).__name__
            or 'Futures timed out' in str(exc))


def _kill_child_provers() -> None:
    """SIGKILL any prover process (z3/boogie) spawned by this process.

    Used only after a hard-deadline cancel: StopVerification interrupts the job's
    JVM threads, but a prover blocked in one long-running query never reads the
    exit command and keeps burning CPU — and Silicon's teardown in turn blocks on
    it. The JVM is in-process (JPype), so provers are direct children of this
    process; killing them unblocks the readers with EOF and the job actor dies
    quickly. Killing is process-wide, so the caller must ensure no concurrent
    job is in flight (it would lose its provers and fail as cancelled).
    """
    me = str(os.getpid())
    for stat_path in glob.glob('/proc/[0-9]*/stat'):
        try:
            with open(stat_path) as f:
                fields = f.read().split()
            comm, ppid = fields[1].strip('()'), fields[3]
            if ppid == me and (comm.startswith('z3') or comm.startswith('boogie')):
                os.kill(int(fields[0]), signal.SIGKILL)
                logging.warning('Killed wedged prover process %s (%s).',
                                fields[0], comm)
        except (OSError, IndexError, ValueError):
            continue


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
                 disable_branch_conditions: bool = False,
                 strict_int: bool = False,
                 force_obligations: bool = False,
                 default_viper_args: List[str] = None,
                 record_dir: str = None):
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
        self._default_viper_args = list(default_viper_args) if default_viper_args else []
        self._sif = sif
        self._float_encoding = float_encoding
        self._bv_size = int_bitops_size
        self._disable_branch_conditions = disable_branch_conditions
        self._strict_int = strict_int
        self._record_dir = record_dir
        self._record_seq = 0
        self._record_lock = threading.Lock()
        if force_obligations:
            # False instead of None: force the obligation encoding (see main.py).
            config.obligation_config.disable_all = False
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
        # Number of verify() calls currently awaiting a ViperServer result; the
        # hard-deadline path only force-kills prover processes when the wedged
        # job is the sole one in flight (killing is process-wide, so a
        # concurrent job would lose its provers too).
        self._inflight = 0

        # JVM() routes JVM System.out to System.err and quiets logback, so the
        # JSON-RPC stream of a stdio-based LSP/MCP frontend on stdout stays clean.
        self.jvm = JVM(config.classpath)
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
               ignore_global: bool = False, viper_args: List[str] = None,
               include_viper: bool = False, translate_only: bool = False,
               int_bitops_size: int = None,
               job_token: str = None) -> VerifyResult:
        """Translate and verify the file at ``path`` and return structured results.

        Multiple calls may run concurrently: translation is serialized but the
        Viper verification overlaps. Pass a ``job_token`` to allow precise
        cancellation of this request via :meth:`cancel`. Set ``ignore_global``
        to skip verification of top-level (module-global) statements.
        ``viper_args`` are extra command-line arguments for the Viper backend
        (the CLI's ``--viper-arg``, as a list). ``include_viper`` returns the
        translated Viper program in ``viper_program``. ``translate_only`` stops
        after translation (mypy + Nagini-to-Viper): success means the file is a
        valid Nagini program; no proof obligations are checked. ``int_bitops_size`` sets
        the bitvector width used to encode int bitwise operations for this
        request; like :meth:`reconfigure` it is sticky (subsequent requests
        keep it) and reloads the Silver resources only when the width changes.
        """
        path = os.path.abspath(path)
        start = time.time()
        viper_args = list(viper_args) if viper_args else []
        # Server-default backend args (the CLI's --viper-arg, given at service
        # launch), applied to every request. The request's own viper_args win:
        # a default is dropped when the request passes the same flag itself.
        if self._default_viper_args:
            given = {a.split('=', 1)[0] for a in viper_args}
            viper_args = [a for a in self._default_viper_args
                          if a.split('=', 1)[0] not in given] + viper_args
        # Snapshot the source before verification: the agent may edit the file
        # while the run is in flight, and the record must show what was verified.
        source = self._read_source(path)
        try:
            if self._can_run_concurrently(arp):
                result = self._verify_concurrent(path, selected, base_dir,
                                                 counterexample,
                                                 ignore_global, viper_args,
                                                 include_viper, job_token,
                                                 translate_only=translate_only,
                                                 int_bitops_size=int_bitops_size)
            else:
                with self._state_lock:
                    result = self._verify_serial(path, selected, base_dir, arp,
                                                 counterexample, ignore_global,
                                                 viper_args, include_viper,
                                                 translate_only=translate_only,
                                                 int_bitops_size=int_bitops_size)
        except Exception as e:
            # Last-resort conversion of internal crashes (translator bugs,
            # unexpected error shapes) into a structured result: callers get a
            # diagnostic instead of a bare exception string, and the full
            # traceback lands in the server log.
            logging.exception('Internal error verifying %s.', path)
            result = VerifyResult(False, [self._point_diagnostic(
                path, 'Internal Nagini error: {}: {} (traceback in server '
                'log).'.format(type(e).__name__, e), 'internal.error')],
                time.time() - start)
        self._record(path, selected, base_dir, viper_args, source, start,
                     result, translate_only)
        return result

    @staticmethod
    def _read_source(path):
        try:
            with open(path, 'rb') as f:
                return f.read()
        except OSError:
            return None

    def _record(self, path, selected, base_dir, viper_args, source, start,
                result, translate_only=False) -> None:
        """Archive one verification attempt under the service's record dir.

        Server-side only — nothing about the recording is visible through the
        MCP tools. Every attempt gets meta.json (effective backend args,
        content hashes of the project's .py files for attempt-series
        attribution) and result.json (full structured result incl. debug
        payloads). Full file contents (the verified file plus its sibling
        .py files) are archived only when a diagnostic carries
        reasonUnknown == 'canceled': those are the budget-exhausted queries
        worth replaying in later SMT experiments. Recording failures must
        never affect verification.
        """
        if not self._record_dir:
            return
        try:
            with self._record_lock:
                self._record_seq += 1
                seq = self._record_seq
            attempt = os.path.join(self._record_dir, 'attempt-%04d' % seq)
            os.makedirs(attempt, exist_ok=True)
            has_canceled = any(
                (d.debug or {}).get('reasonUnknown') == 'canceled'
                for d in result.diagnostics)
            src_dir = os.path.dirname(path)
            project_files = {}
            for name in sorted(os.listdir(src_dir) or []):
                if not name.endswith('.py'):
                    continue
                data = self._read_source(os.path.join(src_dir, name))
                if data is None:
                    continue
                project_files[name] = hashlib.sha256(data).hexdigest()
                if has_canceled:
                    files_dir = os.path.join(attempt, 'files')
                    os.makedirs(files_dir, exist_ok=True)
                    with open(os.path.join(files_dir, name), 'wb') as f:
                        f.write(data)
            if has_canceled and source is not None:
                with open(os.path.join(attempt, 'source.py'), 'wb') as f:
                    f.write(source)
            meta = {
                'seq': seq,
                'path': path,
                'selected': sorted(selected) if selected else None,
                'baseDir': base_dir,
                'effectiveViperArgs': viper_args,
                'backend': self._backend,
                'strictInt': self._strict_int,
                'intBitopsSize': self._bv_size,
                'sourceSha256': (hashlib.sha256(source).hexdigest()
                                 if source is not None else None),
                'projectFiles': project_files,
                'startTime': start,
                'duration': result.duration,
                'success': result.success,
                'cancelled': result.cancelled,
                'translationFailed': result.translation_failed,
                'translateOnly': translate_only,
                'diagnosticCount': len(result.diagnostics),
            }
            with open(os.path.join(attempt, 'meta.json'), 'w') as f:
                json.dump(meta, f, indent=1)
            with open(os.path.join(attempt, 'result.json'), 'w') as f:
                json.dump(result.to_dict(), f, indent=1)
        except Exception:
            logging.exception('Failed to record verification attempt for %s.',
                              path)

    def _apply_bitops_size(self, size: int) -> None:
        """Switch the bitvector width for subsequent translations; sticky, like
        :meth:`reconfigure`. Must be called while holding the state lock.
        No-op when ``size`` is ``None`` or already current.
        """
        if size is None or size == self._bv_size:
            return
        self._bv_size = size
        import nagini_translation.main as main_module
        main_module.sil_programs = load_sil_files(self.jvm, self._bv_size,
                                                  self._sif, self._float_encoding)

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
            'strictInt': self._strict_int,
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
            if options.get('strict_int') is not None:
                self._strict_int = bool(options['strict_int'])
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
                           ignore_global, viper_args, include_viper,
                           job_token, translate_only=False,
                           int_bitops_size=None) -> VerifyResult:
        from nagini_translation.viper_server import (build_carbon_backend_args,
                                                     build_silicon_backend_args,
                                                     get_viper_server_manager)
        manager = get_viper_server_manager(self.jvm)
        start = time.time()
        # 1. Translate and snapshot this job's error-mapping state (serialized).
        with self._state_lock:
            self._apply_bitops_size(int_bitops_size)
            self._reset_obligations()
            try:
                translated = translate(
                    path, self.jvm, self._bv_size,
                    selected=set(selected) if selected else set(), sif=False,
                    base_dir=base_dir, arp=False, counterexample=counterexample,
                    ignore_global=ignore_global, float_encoding=self._float_encoding,
                    strict_int=self._strict_int)
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
            viper_text = str(prog) if include_viper else None
            if translate_only:
                return VerifyResult(True, [], time.time() - start,
                                    viper_program=viper_text)
            snapshot = (dict(error_manager._items),
                        dict(error_manager._conversion_rules))
            error_manager.clear()

        # 2. Submit and await the result lock-free, so jobs overlap in Viper.
        if self._backend == 'carbon':
            backend_args = build_carbon_backend_args(viper_args)
        else:
            backend_args = build_silicon_backend_args(
                viper_args, counterexample, self._disable_branch_conditions)
        job_id = manager.submit(prog, path, backend_args, backend=self._backend)
        if job_token is not None:
            with self._jobs_lock:
                self._jobs[job_token] = job_id
        wall_cap = _hard_wall_seconds(backend_args)
        with self._jobs_lock:
            self._inflight += 1
        try:
            result = manager.await_result(
                job_id, timeout_ms=wall_cap * 1000 if wall_cap else None)
        except Exception as e:
            if wall_cap is not None and _is_await_timeout(e):
                # The backend blew through its own --timeout plus the grace
                # period: cancel the job and, when no other job would be hit,
                # hard-kill the prover processes so the server is immediately
                # usable again; either way report a plain timeout.
                with self._jobs_lock:
                    alone = self._inflight == 1
                logging.warning('Verification of %s exceeded the hard %ss wall '
                                '(backend --timeout plus %ss grace); '
                                'cancelling%s.', path, wall_cap,
                                HARD_DEADLINE_GRACE,
                                ' and killing provers' if alone else
                                '; provers left running (concurrent job in flight)')
                try:
                    manager.cancel_job(job_id)
                finally:
                    if alone:
                        _kill_child_provers()
                return VerifyResult(False, [self._point_diagnostic(
                    path, 'Timeout occurred: verification exceeded %s second(s) '
                    '(hard wall).' % wall_cap,
                    'TimeoutOccurred')], time.time() - start,
                    viper_program=viper_text)
            # Most commonly this is a cancelled job (its actor was stopped).
            logging.debug('Verification job failed or was cancelled.', exc_info=True)
            return VerifyResult(False, [], time.time() - start, cancelled=True,
                                viper_program=viper_text)
        finally:
            with self._jobs_lock:
                self._inflight -= 1
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
                'verifier.error')], duration, viper_program=viper_text)

        # 3. Convert the result with this job's snapshot installed (serialized).
        is_failure = isinstance(result, self.jvm.viper.silver.verifier.Failure)
        if not is_failure:
            return VerifyResult(True, [], duration, viper_program=viper_text)
        with self._state_lock:
            error_manager._items, error_manager._conversion_rules = snapshot
            try:
                it = result.errors().toIterator()
                errors = []
                while it.hasNext():
                    errors.append(it.next())
                try:
                    failure = Failure(errors, self.jvm, modules, self._sif)
                    diagnostics = self._failure_diagnostics(
                        failure, path,
                        smt_state_requested='--smtStateOnError' in viper_args)
                except Exception:
                    # Even a failed conversion must yield the raw Viper
                    # messages rather than crash the request.
                    logging.exception('Failed to convert errors for %s.', path)
                    diagnostics = [self._point_diagnostic(
                        path, self._raw_error_message(e), 'verifier.error')
                        for e in errors] or [self._point_diagnostic(
                            path, 'Internal verifier error (see server log).',
                            'verifier.error')]
            finally:
                error_manager.clear()
        return VerifyResult(False, diagnostics, duration, viper_program=viper_text)

    def _verify_serial(self, path, selected, base_dir, arp,
                       counterexample, ignore_global, viper_args,
                       include_viper, translate_only=False,
                       int_bitops_size=None) -> VerifyResult:
        start = time.time()
        try:
            self._apply_bitops_size(int_bitops_size)
            self._reset_obligations()
            selected_set = set(selected) if selected else set()
            translated = translate(
                path, self.jvm, self._bv_size, selected=selected_set,
                sif=self._sif, base_dir=base_dir, arp=arp,
                counterexample=counterexample, ignore_global=ignore_global,
                float_encoding=self._float_encoding,
                strict_int=self._strict_int)
            if translated is None:
                return VerifyResult(False, [self._point_diagnostic(
                    path, 'Type checking failed.', 'type.error')],
                    time.time() - start, translation_failed=True)
            modules, prog = translated
            viper_text = str(prog) if include_viper else None
            if translate_only:
                return VerifyResult(True, [], time.time() - start,
                                    viper_program=viper_text)
            backend = (ViperVerifier.silicon if self._backend == 'silicon'
                       else ViperVerifier.carbon)
            vresult = verify_program(
                modules, prog, path, self.jvm, viper_args, backend=backend,
                arp=arp, counterexample=counterexample, sif=self._sif,
                disable_branch_conditions=self._disable_branch_conditions)
            duration = time.time() - start
            if vresult is None:
                # main.verify swallows JVM exceptions and returns None.
                return VerifyResult(False, [self._point_diagnostic(
                    path, 'Internal verifier error (see server log).',
                    'verifier.error')], duration, viper_program=viper_text)
            if isinstance(vresult, Failure):
                return VerifyResult(
                    False,
                    self._failure_diagnostics(
                        vresult, path,
                        smt_state_requested='--smtStateOnError' in viper_args),
                    duration, viper_program=viper_text)
            return VerifyResult(True, [], duration, viper_program=viper_text)
        except (TypeException, InvalidProgramException, UnsupportedException) as e:
            return VerifyResult(False, self._exception_diagnostics(e, path),
                                time.time() - start, translation_failed=True)
        except ConsistencyException as e:
            return VerifyResult(False, [self._point_diagnostic(
                path, e.message + ': Translated AST contains inconsistencies.',
                'consistency.error')], time.time() - start, translation_failed=True)

    # Appended to a failure diagnostic served from ViperServer's verification
    # cache while --smtStateOnError is in effect: cache hits replay the stored
    # errors without failure contexts, so no SMT state exists to attach.
    CACHED_STATE_HINT = (
        ' [note: result served from the verification cache, so no SMT state '
        "was collected. Re-verify with viper_args=['--disableCaching'] to "
        'run this member live and collect the state; the cache is kept.]')

    def _failure_diagnostics(self, failure: Failure, path: str,
                             smt_state_requested: bool = False) -> List[Diagnostic]:
        diagnostics = []
        seen = set()
        for error in failure.errors:
            try:
                diag = self._error_diagnostic(error, path)
                if smt_state_requested and diag.debug is None:
                    jvm_error = getattr(error, '_error', None)
                    try:
                        cached = bool(jvm_error is not None
                                      and jvm_error.cached())
                    except Exception:
                        cached = False
                    if cached:
                        diag.message += self.CACHED_STATE_HINT
            except Exception:
                # Rendering a diagnostic must never lose the error itself
                # (internal verifier exceptions produce errors without a
                # mapped reason or position).
                logging.exception('Failed to render diagnostic for %s.', path)
                diag = self._point_diagnostic(
                    path, self._raw_error_message(error), 'verifier.error')
            key = (diag.file, diag.start_line, diag.start_col, diag.code, diag.message)
            if key not in seen:
                seen.add(key)
                diagnostics.append(diag)
        return diagnostics

    def _error_diagnostic(self, error, path: str) -> Diagnostic:
        pos = error.position
        try:
            file_name = pos.file_name
        except Exception:
            file_name = path
        reason = error.reason  # None for internal verifier exceptions
        vias = [(str(r), str(p))
                for r, p in ((reason.vias if reason is not None else None)
                             or error._vias or [])]
        try:
            reason_pos = (reason.position.line, reason.position.column)
        except Exception:
            reason_pos = None
        return Diagnostic(
            file=file_name,
            start_line=pos.line, start_col=pos.column,
            end_line=pos.line_end, end_col=pos.column_end,
            message=(error.message if reason is not None
                     else self._raw_error_message(error)),
            code=error.full_id,
            reason=reason.string(False) if reason is not None else None,
            reason_position=reason_pos,
            vias=vias,
            counterexample=(str(error._inputs)
                            if error._inputs is not None else None),
            branch_conditions=list(error.bcs) if error.bcs else [],
            debug=_debug_payload(error),
        )

    @staticmethod
    def _raw_error_message(error) -> str:
        """Best-effort message for an error whose normal rendering is
        unavailable (no reason mapping, exotic error class)."""
        for attr in ('readable_message', 'readableMessage', 'text'):
            try:
                value = getattr(error, attr)
                return str(value() if callable(value) else value)
            except Exception:
                continue
        return 'Internal verifier error (see server log).'

    def _exception_diagnostics(self, e, path: str) -> List[Diagnostic]:
        if isinstance(e, (InvalidProgramException, UnsupportedException)):
            if isinstance(e, InvalidProgramException):
                code = 'invalid.program'
                message = ('Invalid program: ' +
                           invalid_program_message(e.code, e.message))
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
                # mypy gives a 1-based start column and an (exclusive) end
                # position when available; Diagnostic uses 0-based columns (the
                # same convention as verification errors here). Fall back to a
                # zero-width span at column 0 for line-only messages.
                col = int(parts['col']) - 1 if parts['col'] else 0
                end_line = int(parts['end_line']) if parts['end_line'] else line
                end_col = int(parts['end_col']) if parts['end_col'] else col
                diagnostics.append(Diagnostic(
                    file=file, start_line=line, start_col=col, end_line=end_line,
                    end_col=end_col, message='Type error: ' + parts['msg'],
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
    'strictInt': 'strict_int',
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
    parser.add_argument('--strict-int', action='store_true', default=False,
                        help='require exact int type (type(x) == int) rather '
                             'than subtype (isinstance(x, int)) in many places')
    parser.add_argument('--force-obligations', action='store_true', default=False,
                        help='force use of the obligations encoding used to '
                             'verify liveness properties')
    parser.add_argument('--viper-arg', default=None,
                        help='arguments forwarded to the Viper backend on every '
                             'verification request, separated by commas (same '
                             "syntax as the CLI's --viper-arg; a request's own "
                             'viper_args override same-name flags)')
    parser.add_argument('--record-dir', default=None,
                        help='archive every verification attempt (source '
                             'snapshot, effective backend args, full result '
                             'incl. debug payloads) into this directory; '
                             'server-side only, invisible to MCP clients')
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
        disable_branch_conditions=args.disable_branch_conditions,
        strict_int=args.strict_int, force_obligations=args.force_obligations,
        default_viper_args=args.viper_arg.split(',') if args.viper_arg else None,
        record_dir=args.record_dir)


def make_service(args: argparse.Namespace) -> VerificationService:
    """Build a :class:`VerificationService` from parsed CLI arguments."""
    return VerificationService(**service_kwargs_from_args(args))
