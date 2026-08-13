"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""
Model Context Protocol frontend for Nagini.

Exposes the shared :class:`VerificationService` as MCP tools (over stdio) so an
AI agent can verify files, methods, or inline snippets and receive structured
diagnostics, and can cancel runs or flush the cache.
"""


import argparse
import asyncio
import json
import logging
import os
import shutil
import sys
import tempfile

from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from nagini_translation.service import (add_service_arguments, make_service,
                                        options_to_kwargs)


mcp = FastMCP('nagini')
_service = None
# Multiple verifications can run at once; the service serializes only the fast
# translation step internally.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='nagini-verify')


# Inline debug payloads must fit Claude Code's per-result token limit (25k
# tokens by default) or the whole result gets file-redirected — which agents
# in practice never read (and the redirect swallows even the diagnostic
# message, so an oversized payload is WORSE than none). Everything dropped
# here is still recorded server-side (--record-dir) in full.
#
# Strategy: measure the whole serialized result and degrade the debug
# payloads stage by stage — least-consulted (expert-tier) fields first, as
# observed in real agent runs — until the result fits. `reasonUnknown` (the
# field agents actually act on), the truncation markers, and the diagnostic
# message itself always survive.
_BULK_DEBUG_FIELDS = ('proverEmits', 'preambleAssumptions')
# Whole-result char budget. Silicon terms are symbol-dense (~2.5 chars/token),
# so 50k chars keeps a comfortable margin under the 25k-token cap.
_RESULT_BUDGET = 50_000
_STATE_STUB_CHARS = 1_500  # per state projection (store/heap/oldHeaps)
_BRANCH_CAP = 20           # branch conditions kept in stage 4
_ASSERTION_STUB_CHARS = 2_000


def _mark(dbg: dict, field: str, note) -> None:
    dbg.setdefault('omitted', {})[field] = note


def _degrade(dbg: dict, stage: int) -> None:
    """Destructively degrade one debug dict to the given stage (cumulative).

    Ordered by information lost per byte recovered: state stubs first (the
    heap/store strings are almost always the byte-dominant fields, and a stub
    still shows the store variables and heap shape), then the fields agents
    were never observed to consult, then the progressively harsher cuts.
    """
    if stage >= 1 and isinstance(dbg.get('state'), dict):
        for k, v in dbg['state'].items():
            if isinstance(v, str) and len(v) > _STATE_STUB_CHARS:
                dbg['state'][k] = v[:_STATE_STUB_CHARS] + '…[truncated]'
    if stage >= 2 and ('macroDecls' in dbg or 'functionDecls' in dbg):
        for f in ('macroDecls', 'functionDecls'):
            if dbg.pop(f, None) is not None:
                _mark(dbg, f, 'dropped')
    if stage >= 3 and 'assumptions' in dbg:
        _mark(dbg, 'assumptions', len(dbg.pop('assumptions') or []))
    if stage >= 4 and isinstance(dbg.get('branchConditions'), list) \
            and len(dbg['branchConditions']) > _BRANCH_CAP:
        _mark(dbg, 'branchConditions',
              len(dbg['branchConditions']) - _BRANCH_CAP)
        dbg['branchConditions'] = dbg['branchConditions'][:_BRANCH_CAP]
    if stage >= 5 and dbg.pop('state', None) is not None:
        _mark(dbg, 'state', 'dropped')
    if stage >= 6 and dbg.pop('branchConditions', None) is not None:
        _mark(dbg, 'branchConditions', 'dropped')
    if stage >= 7 and isinstance(dbg.get('failedAssertion'), str) \
            and len(dbg['failedAssertion']) > _ASSERTION_STUB_CHARS:
        dbg['failedAssertion'] = (dbg['failedAssertion'][:_ASSERTION_STUB_CHARS]
                                  + '…[truncated]')


_MAX_STAGE = 7


def _as_selected(methods) -> Optional[set]:
    """Normalize a list of method names to a set, or None for 'whole file'.

    Tolerates a bare string (some MCP clients send one despite the declared
    list schema) by treating it as a single name.
    """
    if not methods:
        return None
    if isinstance(methods, str):
        return {methods}
    return set(methods)


def _slim_debug(result: dict) -> dict:
    debugs = []
    for d in result.get('diagnostics', []):
        dbg = d.get('debug')
        if not dbg:
            continue
        dbg = {k: v for k, v in dbg.items() if k not in _BULK_DEBUG_FIELDS}
        d['debug'] = dbg
        debugs.append(dbg)
    if not debugs:
        return result
    # Degrade as little as possible: while the whole result is over budget,
    # advance only the LARGEST remaining payload one stage — small
    # diagnostics keep their full payloads.
    stages = {id(dbg): 0 for dbg in debugs}
    while len(json.dumps(result, default=str)) > _RESULT_BUDGET:
        candidates = [dbg for dbg in debugs if stages[id(dbg)] < _MAX_STAGE]
        if not candidates:
            break  # nothing left to degrade (oversize is outside the payloads)
        worst = max(candidates, key=lambda dbg: len(json.dumps(dbg, default=str)))
        stages[id(worst)] += 1
        _degrade(worst, stages[id(worst)])
    return result



async def _run(fn):
    try:
        return await asyncio.get_event_loop().run_in_executor(_executor, fn)
    except Exception:
        # The MCP layer reports tool exceptions as a bare str(e); make sure
        # the traceback is at least recoverable from the server's stderr.
        logging.exception('Verification tool crashed.')
        raise


@mcp.tool()
async def verify_file(path: str, methods: Optional[List[str]] = None,
                      counterexample: bool = False,
                      ignore_global: bool = False,
                      base_dir: Optional[str] = None,
                      viper_args: Optional[List[str]] = None,
                      include_viper: bool = False,
                      translate_only: bool = False,
                      int_bitops_size: Optional[int] = None,
                      job_token: Optional[str] = None) -> dict:
    """Verify a Nagini Python file.

    `path` should be absolute; relative paths are resolved against the server
    process's working directory (set by the MCP client, not the caller), which
    is usually not what you want.

    Returns structured diagnostics: a list of {file, startLine, startCol,
    endLine, endCol, severity, code, message, reason, counterexample,
    branchConditions, vias}, plus `success` and `duration`. Optionally restrict
    to a list of `methods`; each entry is a top-level function by its bare name
    (e.g. `my_func`), a method as `ClassName.method_name` (its bare name also
    matches), or a whole class by `ClassName` to verify all its methods.
    Passing several methods in one call is cheaper than one call per method:
    the file is translated once and the selected methods are verified in
    parallel. Set `ignore_global` to skip verification of top-level
    (module-global) statements.

    `base_dir` is the package root used to resolve intra-package imports during
    type checking; set it for a file that is part of a package (so its imports
    resolve), and leave it unset for a standalone file. Pass a `job_token` to
    allow precisely cancelling this run via the `cancel` tool. Multiple
    verifications may run concurrently.

    `viper_args` are extra command-line arguments passed to the Viper backend,
    e.g. `["--timeout=60"]` for a per-run verification timeout in seconds (the
    CLI's `--viper-arg`, as a list). `include_viper` returns the translated
    Viper program in `viperProgram`; even a small file translates to hundreds
    of lines, so only request it when needed. `translate_only` stops after
    translation (mypy + Nagini-to-Viper): fast validity check that the file is
    a well-formed Nagini program; no proof obligations are checked.
    """
    selected = _as_selected(methods)
    result = await _run(lambda: _service.verify(
        path, selected=selected, counterexample=counterexample, base_dir=base_dir,
        ignore_global=ignore_global, viper_args=viper_args,
        include_viper=include_viper, translate_only=translate_only,
        int_bitops_size=int_bitops_size, job_token=job_token))
    return _slim_debug(result.to_dict())


@mcp.tool()
async def verify_method(path: str, methods: List[str],
                        counterexample: bool = False,
                        viper_args: Optional[List[str]] = None,
                        include_viper: bool = False,
                        translate_only: bool = False,
                        int_bitops_size: Optional[int] = None,
                        job_token: Optional[str] = None) -> dict:
    """Verify selected methods of a file (fast, via Nagini's --select).

    `path` should be absolute (see `verify_file`). `methods` is a list of
    member names: a top-level function by its bare name (e.g. `["my_func"]`),
    a method as `ClassName.method_name` (its bare name also matches), or a
    whole class by `ClassName`. Verifying several methods in one call is
    cheaper than one call per method: one translation, verified in parallel.
    """
    result = await _run(lambda: _service.verify(
        path, selected=_as_selected(methods), counterexample=counterexample,
        viper_args=viper_args, include_viper=include_viper,
        translate_only=translate_only,
        int_bitops_size=int_bitops_size, job_token=job_token))
    return _slim_debug(result.to_dict())


@mcp.tool()
async def verify_snippet(code: str, counterexample: bool = False,
                         ignore_global: bool = False,
                         viper_args: Optional[List[str]] = None,
                         include_viper: bool = False,
                         translate_only: bool = False,
                         int_bitops_size: Optional[int] = None,
                         job_token: Optional[str] = None) -> dict:
    """Verify an inline snippet of Nagini Python code (written to a temp file).

    Set `ignore_global` to skip verification of top-level statements. The other
    parameters are as in `verify_file`.
    """
    tmp_dir = tempfile.mkdtemp(prefix='nagini_mcp_')
    tmp_path = os.path.join(tmp_dir, 'snippet.py')
    try:
        with open(tmp_path, 'w') as f:
            f.write(code)
        result = await _run(lambda: _service.verify(
            tmp_path, counterexample=counterexample, base_dir=tmp_dir,
            ignore_global=ignore_global, viper_args=viper_args,
            include_viper=include_viper, translate_only=translate_only,
            int_bitops_size=int_bitops_size, job_token=job_token))
        return _slim_debug(result.to_dict())
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@mcp.tool()
def configure(options: dict) -> dict:
    """Change verification options for subsequent requests; returns the effective
    configuration.

    Recognized keys: `verifier` ('silicon' or 'carbon'), `z3Path`, `boogiePath`,
    `mypyPath`, `sif`, `intBitopsSize`, `floatEncoding`, `useViperServer`,
    `disableBranchConditions`, `strictInt`. `viperJarPath` cannot be changed after startup and
    is ignored. Unknown or null keys are ignored. Changing
    `sif`/`intBitopsSize`/`floatEncoding` reloads the Silver resources;
    already-running verifications are unaffected.
    """
    return _service.reconfigure(**options_to_kwargs(options))


@mcp.tool()
def cancel(job_token: Optional[str] = None) -> dict:
    """Cancel verification: a specific run if `job_token` is given, else all."""
    _service.cancel(job_token=job_token)
    return {'cancelled': True, 'jobToken': job_token}


@mcp.tool()
def flush_cache() -> dict:
    """Clear the ViperServer result cache."""
    _service.flush_cache()
    return {'flushed': True}


def main():
    parser = argparse.ArgumentParser(description='Nagini MCP server (stdio).')
    add_service_arguments(parser)
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.WARNING))
    global _service
    _service = make_service(args)
    try:
        mcp.run()
    finally:
        try:
            _service.shutdown()
        except Exception:
            logging.exception('Error shutting down service.')
        # The stdio transport may already have closed these streams by the time
        # we get here; flushing a closed stream raises ValueError, so ignore it.
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except (ValueError, OSError):
                pass
        os._exit(0)


if __name__ == '__main__':
    main()
