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
import logging
import os
import shutil
import sys
import tempfile

from concurrent.futures import Future, ThreadPoolExecutor
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from nagini_translation.service import (add_service_arguments, make_service,
                                        options_to_kwargs)


mcp = FastMCP('nagini')
_service_future: Optional[Future] = None
# Multiple verifications can run at once; the service serializes only the fast
# translation step internally.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='nagini-verify')


def _get_service():
    """Wait for the service to finish booting. Blocks; call only from
    `_executor` threads, never from the event loop (FastMCP runs even sync
    tools on the loop)."""
    assert _service_future is not None
    return _service_future.result()


def _service_if_ready():
    """The booted service, or None while it is still booting or failed to boot."""
    if (_service_future is not None and _service_future.done()
            and _service_future.exception() is None):
        return _service_future.result()
    return None


async def _run(fn):
    return await asyncio.get_event_loop().run_in_executor(_executor, fn)


@mcp.tool()
async def verify_file(path: str, method: Optional[str] = None,
                      counterexample: bool = False,
                      ignore_global: bool = False,
                      base_dir: Optional[str] = None,
                      viper_args: Optional[List[str]] = None,
                      include_viper: bool = False,
                      job_token: Optional[str] = None) -> dict:
    """Verify a Nagini Python file.

    `path` should be absolute; relative paths are resolved against the server
    process's working directory (set by the MCP client, not the caller), which
    is usually not what you want.

    Returns structured diagnostics: a list of {file, startLine, startCol,
    endLine, endCol, severity, code, message, reason, counterexample,
    branchConditions, vias}, plus `success` and `duration`. Optionally restrict
    to a single `method`: a top-level function by its bare name (e.g. `my_func`),
    a method as `ClassName.method_name` (its bare name also matches), or a whole
    class by `ClassName` to verify all its methods. Set `ignore_global` to skip
    verification of top-level (module-global) statements.

    `base_dir` is the package root used to resolve intra-package imports during
    type checking; set it for a file that is part of a package (so its imports
    resolve), and leave it unset for a standalone file. Pass a `job_token` to
    allow precisely cancelling this run via the `cancel` tool. Multiple
    verifications may run concurrently.

    `viper_args` are extra command-line arguments passed to the Viper backend,
    e.g. `["--timeout=60"]` for a per-run verification timeout in seconds (the
    CLI's `--viper-arg`, as a list). `include_viper` returns the translated
    Viper program in `viperProgram`; even a small file translates to hundreds
    of lines, so only request it when needed.
    """
    selected = {method} if method else None
    result = await _run(lambda: _get_service().verify(
        path, selected=selected, counterexample=counterexample, base_dir=base_dir,
        ignore_global=ignore_global, viper_args=viper_args,
        include_viper=include_viper, job_token=job_token))
    return result.to_dict()


@mcp.tool()
async def verify_method(path: str, method: str, counterexample: bool = False,
                        viper_args: Optional[List[str]] = None,
                        include_viper: bool = False,
                        job_token: Optional[str] = None) -> dict:
    """Verify only a single method of a file (fast, via Nagini's --select).

    `path` should be absolute (see `verify_file`). `method` names a top-level
    function by its bare name (e.g. `my_func`), a method as `ClassName.method_name`
    (its bare name also matches), or a whole class by `ClassName`. The other
    parameters are as in `verify_file`.
    """
    result = await _run(lambda: _get_service().verify(
        path, selected={method}, counterexample=counterexample,
        viper_args=viper_args, include_viper=include_viper,
        job_token=job_token))
    return result.to_dict()


@mcp.tool()
async def verify_snippet(code: str, counterexample: bool = False,
                         ignore_global: bool = False,
                         viper_args: Optional[List[str]] = None,
                         include_viper: bool = False,
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
        result = await _run(lambda: _get_service().verify(
            tmp_path, counterexample=counterexample, base_dir=tmp_dir,
            ignore_global=ignore_global, viper_args=viper_args,
            include_viper=include_viper, job_token=job_token))
        return result.to_dict()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@mcp.tool()
async def configure(options: dict) -> dict:
    """Change verification options for subsequent requests; returns the effective
    configuration.

    Recognized keys: `verifier` ('silicon' or 'carbon'), `z3Path`, `boogiePath`,
    `mypyPath`, `sif`, `intBitopsSize`, `floatEncoding`, `useViperServer`,
    `disableBranchConditions`. `viperJarPath` cannot be changed after startup and
    is ignored. Unknown or null keys are ignored. Changing
    `sif`/`intBitopsSize`/`floatEncoding` reloads the Silver resources;
    already-running verifications are unaffected.
    """
    return await _run(lambda: _get_service().reconfigure(**options_to_kwargs(options)))


@mcp.tool()
def cancel(job_token: Optional[str] = None) -> dict:
    """Cancel verification: a specific run if `job_token` is given, else all."""
    service = _service_if_ready()
    if service is not None:
        service.cancel(job_token=job_token)
    return {'cancelled': service is not None, 'jobToken': job_token}


@mcp.tool()
def flush_cache() -> dict:
    """Clear the ViperServer result cache."""
    service = _service_if_ready()
    if service is not None:
        service.flush_cache()
    return {'flushed': service is not None}


def main():
    parser = argparse.ArgumentParser(description='Nagini MCP server (stdio).')
    add_service_arguments(parser)
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.WARNING))
    global _service_future
    # The JVM-backed service boots in the background (see `main`) so the MCP handshake is answered
    # immediately instead of after JVM startup, which can exceed common client startup timeouts.
    _service_future = ThreadPoolExecutor(
        max_workers=1, thread_name_prefix='nagini-boot').submit(make_service, args)
    try:
        mcp.run()
    finally:
        try:
            service = _service_if_ready()
            if service is not None:
                service.shutdown()
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
