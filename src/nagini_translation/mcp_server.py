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
import re
import shutil
import sys
import tempfile

from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from mcp.server.mcpserver import MCPServer

from nagini_translation.service import (add_service_arguments, make_service,
                                        options_to_kwargs)


mcp = MCPServer('nagini')
_service = None
# Multiple verifications can run at once; the service serializes only the fast
# translation step internally.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='nagini-verify')


# Inline debug payloads must fit Claude Code's per-result size limit or the
# whole result gets file-redirected — which agents in practice rarely read
# (and the redirect swallows even the diagnostic message, so an oversized
# payload is WORSE than none). Everything dropped here is still recorded
# server-side (--record-dir) in full.
#
# Strategy: measure the whole serialized result and shrink the debug payloads
# step by step — least information lost per byte recovered first, as measured
# on archived payloads — until the result fits. `reasonUnknown` (the field
# agents actually act on), `failingCheck`, the truncation markers and the
# diagnostic message itself always survive.
_BULK_DEBUG_FIELDS = ('proverEmits', 'preambleAssumptions',
                      # 2026-08-13: across nine full benchmark runs no agent ever
                      # consulted either of these; they remain in the recorded
                      # result.json (--record-dir) for offline replay.
                      'macroDecls', 'functionDecls',
                      # a server-side path to a prover session file
                      'sessionLog')
# Whole-result char budget, measured on the indented JSON the MCP layer
# sends (2-4% larger than the compact form). Claude Code redirects a result
# to a file at about 50k chars of that text; 40k keeps a margin below it.
_RESULT_BUDGET = 40_000
_ENTRY_CHARS = 1_000           # an assumption or branch-condition term (step 1)
_ASSUMPTION_CAPS = (20, 10)    # the assumption cap after steps 2 and 3
_STATE_STUB_CHARS = 1_500      # per state projection (store/heap/oldHeaps)
_QUANTIFIER_BODY_CHARS = 400   # a quantifier body; its triggers stay whole
_BRANCH_CAP = 20               # branch conditions kept
_EXCERPT_STUB_CHARS = 6_000    # the failing member's Viper text
_ASSERTION_STUB_CHARS = 2_000
_DEBUG_KEEP = 3                # diagnostics that keep a payload when the rest must go
_DIAGS_KEEP = 10               # diagnostics kept when even that is not enough


def _mark(dbg: dict, field: str, note) -> None:
    dbg.setdefault('omitted', {})[field] = note


def _truncate(text, limit: int):
    if isinstance(text, str) and len(text) > limit:
        return text[:limit] + '…[truncated]'
    return text


def _cap(dbg: dict, field: str, cap: int) -> None:
    """Keep the newest `cap` entries of a list field, extending its note."""
    entries = dbg.get(field)
    if not isinstance(entries, list) or len(entries) <= cap:
        return
    note = '%d older ones beyond the cap of %d' % (len(entries) - cap, cap)
    prev = (dbg.get('omitted') or {}).get(field)
    _mark(dbg, field, '%s; %s' % (prev, note) if isinstance(prev, str) else note)
    dbg[field] = entries[-cap:]


def _drop(dbg: dict, field: str) -> None:
    if dbg.pop(field, None) is not None:
        _mark(dbg, field, 'dropped')


def _step_entries(dbg: dict) -> None:
    # A single assumption term can run to 100k+ chars; the list is what the
    # diagnosis reads, so cut the terms before touching the list.
    for field in ('assumptions', 'branchConditions'):
        if isinstance(dbg.get(field), list):
            dbg[field] = [_truncate(e, _ENTRY_CHARS) for e in dbg[field]]


def _step_state_stubs(dbg: dict) -> None:
    state = dbg.get('state')
    if isinstance(state, dict):
        for k, v in state.items():
            state[k] = _truncate(v, _STATE_STUB_CHARS)


def _step_assumptions_count(dbg: dict) -> None:
    if 'assumptions' in dbg:
        _mark(dbg, 'assumptions', len(dbg.pop('assumptions') or []))
    for q in dbg.get('quantifiers') or []:
        q['body'] = _truncate(q.get('body'), _QUANTIFIER_BODY_CHARS)


def _step_drop_state(dbg: dict) -> None:
    _drop(dbg, 'state')
    excerpt = dbg.get('viperExcerpt') or {}
    if excerpt.get('quantified'):
        _mark(dbg, 'viperExcerpt.quantified', len(excerpt.pop('quantified')))


def _step_drop_paths(dbg: dict) -> None:
    _drop(dbg, 'branchConditions')
    _drop(dbg, 'quantifiers')


def _step_stubs(dbg: dict) -> None:
    excerpt = dbg.get('viperExcerpt') or {}
    if 'viper' in excerpt:
        excerpt['viper'] = _truncate(excerpt['viper'], _EXCERPT_STUB_CHARS)
    dbg['failedAssertion'] = _truncate(dbg.get('failedAssertion'), _ASSERTION_STUB_CHARS)


# One payload's shrinking steps, applied in order, each once.
_STEPS = (
    _step_entries,
    lambda dbg: _cap(dbg, 'assumptions', _ASSUMPTION_CAPS[0]),
    lambda dbg: _cap(dbg, 'assumptions', _ASSUMPTION_CAPS[1]),
    _step_state_stubs,
    _step_assumptions_count,
    lambda dbg: _cap(dbg, 'branchConditions', _BRANCH_CAP),
    _step_drop_state,
    _step_drop_paths,
    _step_stubs,
)


def _size(obj) -> int:
    return len(json.dumps(obj, default=str, indent=2))

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


_SYMBOL = re.compile(r'[A-Za-z_$][\w$]*@\d+@\d+')
_ASSUMPTION_CAP = 40
_QUANTIFIER_CAP = 20


def _keep_relevant(dbg: dict, field: str, text, cap: int) -> None:
    """Keep only the entries of the list `dbg[field]` that share a symbol with
    the failed assertion (they are the ones that can explain it), and of those
    the newest along the path up to `cap`; `text` renders an entry for the
    symbol test. The full list stays in the recorded result.json. Runs before
    the budget loop, so relevant entries survive slimming that would
    previously have dropped the whole list."""
    entries = dbg.get(field)
    if not isinstance(entries, list) or not entries:
        return
    syms = set(_SYMBOL.findall(str(dbg.get('failedAssertion', ''))))
    relevant = [e for e in entries if not syms or any(s in text(e) for s in syms)]
    kept = relevant[-cap:]
    if len(kept) < len(entries):
        notes = []
        if len(relevant) < len(entries):
            notes.append('%d not sharing a symbol with failedAssertion'
                         % (len(entries) - len(relevant)))
        if len(kept) < len(relevant):
            notes.append('%d older ones beyond the cap of %d' % (len(relevant) - len(kept), cap))
        _mark(dbg, field, ', '.join(notes))
    dbg[field] = kept


def _filter_assumptions(dbg: dict) -> None:
    _keep_relevant(dbg, 'assumptions', str, _ASSUMPTION_CAP)


def _filter_quantifiers(dbg: dict) -> None:
    _keep_relevant(dbg, 'quantifiers', lambda q: q.get('body', '') + ' '.join(
        t for ts in q.get('triggers', []) for t in ts), _QUANTIFIER_CAP)


def _share_excerpts(diagnostics: list) -> None:
    """A member's Viper excerpt travels once: the first diagnostic in the
    member carries it, the later ones point at that diagnostic's index."""
    first = {}
    for i, d in enumerate(diagnostics):
        excerpt = (d.get('debug') or {}).get('viperExcerpt')
        if not excerpt or excerpt.get('member') is None:
            continue
        holder = first.setdefault(excerpt['member'], i)
        if holder != i:
            d['debug']['viperExcerpt'] = {'member': excerpt['member'], 'sameAs': holder}


def _slim_debug(result: dict) -> dict:
    if _service.plain_diagnostics:
        # Plain diagnostics (--plain-diagnostics): no debug payloads, no phase
        # timings, no pointer to the recorded archive.
        result.pop('timings', None)
        result.pop('recordedAt', None)
        for d in result.get('diagnostics', []):
            d.pop('debug', None)
        return result
    diagnostics = result.get('diagnostics', [])
    debugs = []
    for d in diagnostics:
        dbg = d.get('debug')
        if not dbg:
            continue
        dbg = {k: v for k, v in dbg.items() if k not in _BULK_DEBUG_FIELDS}
        _filter_assumptions(dbg)
        _filter_quantifiers(dbg)
        d['debug'] = dbg
        debugs.append(dbg)
    if not debugs:
        return result
    _share_excerpts(diagnostics)
    # Shrink as little as possible: while the whole result is over budget,
    # advance only the LARGEST remaining payload one step — small
    # diagnostics keep their full payloads. When every payload is at the last
    # step, strip the payloads of the last diagnostics down to _DEBUG_KEEP,
    # then cut the diagnostic list itself down to _DIAGS_KEEP.
    steps = {id(dbg): 0 for dbg in debugs}
    while _size(result) > _RESULT_BUDGET:
        candidates = [dbg for dbg in debugs if steps[id(dbg)] < len(_STEPS)]
        if candidates:
            worst = max(candidates, key=_size)
            steps[id(worst)] += 1
            _STEPS[steps[id(worst)] - 1](worst)
            continue
        live = {id(dbg) for dbg in debugs}
        holders = [d for d in diagnostics if id(d.get('debug')) in live]
        if len(holders) > _DEBUG_KEEP:
            last = holders[-1]
            debugs = [dbg for dbg in debugs if dbg is not last['debug']]
            last['debug'] = {'omitted': {'debug': 'dropped'}}
            continue
        if len(diagnostics) > _DIAGS_KEEP:
            diagnostics.pop()
            result['diagnosticsDropped'] = result.get('diagnosticsDropped', 0) + 1
            continue
        break  # nothing left to shrink (oversize is outside the payloads)
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
    branchConditions, vias}, plus `success` and `duration` — and two abnormal-
    end flags: `cancelled` (the job was stopped, e.g. via the `cancel` tool)
    and `crashed` (the verification backend died with an exception, reported
    in a `verifier.crashed` diagnostic; unlike a timeout, retrying an
    identical crashed run is usually pointless). Optionally restrict
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
    CLI's `--viper-arg`, as a list); they override same-named backend defaults,
    and a rejected command line is reported as an `invalid.viper.args`
    diagnostic. `include_viper` returns the whole translated program in
    `viperProgram` (thousands of lines for a large module). `translate_only`
    stops after
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
    `disableBranchConditions`. `viperJarPath` cannot be changed after startup and
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
