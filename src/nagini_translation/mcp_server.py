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

from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from mcp.server.fastmcp import FastMCP

from nagini_translation.service import add_service_arguments, make_service


mcp = FastMCP('nagini')
_service = None
# Multiple verifications can run at once; the service serializes only the fast
# translation step internally.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='nagini-verify')


async def _run(fn):
    return await asyncio.get_event_loop().run_in_executor(_executor, fn)


@mcp.tool()
async def verify_file(path: str, method: Optional[str] = None,
                      counterexample: bool = False,
                      base_dir: Optional[str] = None,
                      job_token: Optional[str] = None) -> dict:
    """Verify a Nagini Python file.

    Returns structured diagnostics: a list of {file, startLine, startCol,
    endLine, endCol, severity, code, message, reason, counterexample,
    branchConditions, vias}, plus `success` and `duration`. Optionally restrict
    to a single `method` (qualified name, e.g. `MyClass.my_method`). Pass a
    `job_token` to allow precisely cancelling this run via the `cancel` tool.
    Multiple verifications may run concurrently.
    """
    selected = {method} if method else None
    result = await _run(lambda: _service.verify(
        path, selected=selected, counterexample=counterexample, base_dir=base_dir,
        job_token=job_token))
    return result.to_dict()


@mcp.tool()
async def verify_method(path: str, method: str, counterexample: bool = False,
                        job_token: Optional[str] = None) -> dict:
    """Verify only a single method of a file (fast, via Nagini's --select)."""
    result = await _run(lambda: _service.verify(
        path, selected={method}, counterexample=counterexample,
        job_token=job_token))
    return result.to_dict()


@mcp.tool()
async def verify_snippet(code: str, counterexample: bool = False,
                         job_token: Optional[str] = None) -> dict:
    """Verify an inline snippet of Nagini Python code (written to a temp file)."""
    tmp_dir = tempfile.mkdtemp(prefix='nagini_mcp_')
    tmp_path = os.path.join(tmp_dir, 'snippet.py')
    try:
        with open(tmp_path, 'w') as f:
            f.write(code)
        result = await _run(lambda: _service.verify(
            tmp_path, counterexample=counterexample, base_dir=tmp_dir,
            job_token=job_token))
        return result.to_dict()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


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
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)


if __name__ == '__main__':
    main()
