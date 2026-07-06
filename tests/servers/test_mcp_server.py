"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


import asyncio
import json
import os
import sys
import tempfile

import pytest

pytest.importorskip("mcp")

from nagini_translation import mcp_server


_DIAG_KEYS = {"file", "startLine", "startCol", "endLine", "endCol", "severity",
              "code", "source", "message"}


def _tool_result_payload(result):
    """Extract the JSON dict a tool returned from an MCP CallToolResult."""
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    for content in result.content:
        if getattr(content, "type", None) == "text":
            return json.loads(content.text)
    raise AssertionError("no textual content in tool result")


def _run_stdio_smoke(pass_file):
    """Drive the server as a real MCP client would: spawn it as a subprocess and
    talk to it over stdio. Returns (tool names, verify result, server stderr)."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "nagini_translation.mcp_server", "--log", "WARNING"],
        # Inherit the parent environment so JAVA_HOME / jar paths reach the JVM,
        # just as an MCP client is expected to pass them through.
        env=dict(os.environ),
    )

    async def _go(errlog):
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=180)
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                result = await asyncio.wait_for(
                    session.call_tool("verify_file", {"path": pass_file}),
                    timeout=300)
                return names, result

    with tempfile.TemporaryFile(mode="w+") as errlog:
        names, result = asyncio.run(_go(errlog))
        errlog.seek(0)
        server_stderr = errlog.read()
    return names, result, server_stderr


def test_stdio_transport_end_to_end_and_clean_shutdown(pass_file):
    # Integration smoke test over the actual stdio transport and process
    # lifecycle (the in-process tool-call tests below never exercise those).
    # Starts its own JVM/ViperServer, so it is skipped if that is unavailable.
    pytest.importorskip("mcp.client.stdio")
    try:
        names, result, server_stderr = _run_stdio_smoke(pass_file)
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip("MCP stdio server could not be started: {}".format(e))

    # The full tool surface is advertised over the wire.
    assert {"verify_file", "verify_method", "verify_snippet",
            "configure", "cancel", "flush_cache"}.issubset(names)

    # A structured result round-trips through the transport, not just in-process.
    payload = _tool_result_payload(result)
    assert payload["success"] is True
    assert payload["diagnostics"] == []

    # Closing the client pipe shuts the server down cleanly; in particular it
    # must not trip the "I/O operation on closed file" flush error on exit.
    assert "I/O operation on closed file" not in server_stderr
    assert "Traceback (most recent call last)" not in server_stderr


def test_verify_file_reports_structured_failure(service, fail_file):
    mcp_server._service = service
    result = asyncio.run(mcp_server.verify_file(fail_file))
    assert result["success"] is False
    assert result["diagnostics"]
    diag = result["diagnostics"][0]
    assert _DIAG_KEYS.issubset(diag.keys())
    assert "postcondition" in diag["code"]
    assert diag["startLine"] == 5  # Nagini-native 1-indexed line


def test_verify_file_success(service, pass_file):
    mcp_server._service = service
    result = asyncio.run(mcp_server.verify_file(pass_file))
    assert result["success"] is True
    assert result["diagnostics"] == []


def test_verify_method_restricts_to_one_method(service, fail_file):
    mcp_server._service = service
    result = asyncio.run(mcp_server.verify_method(fail_file, "add"))
    assert "success" in result
    assert "diagnostics" in result


def test_verify_method_excludes_error_outside_selection(service, mixed_file):
    """Selecting a method must ignore verification errors in other methods."""
    mcp_server._service = service
    # Baseline: verifying the whole file surfaces the error in `failing`.
    full = asyncio.run(mcp_server.verify_file(mixed_file))
    assert full["success"] is False
    assert any("postcondition" in d["code"] for d in full["diagnostics"])
    # Selecting only the correct method excludes the error in `failing`.
    ok = asyncio.run(mcp_server.verify_method(mixed_file, "passing"))
    assert ok["success"] is True
    assert ok["diagnostics"] == []
    # Selecting the faulty method still reports its error.
    bad = asyncio.run(mcp_server.verify_method(mixed_file, "failing"))
    assert bad["success"] is False
    assert any("postcondition" in d["code"] for d in bad["diagnostics"])


def test_verify_snippet_inline_code(service, pass_src):
    mcp_server._service = service
    result = asyncio.run(mcp_server.verify_snippet(pass_src))
    assert result["success"] is True


def test_verify_snippet_inline_failure(service, fail_src):
    mcp_server._service = service
    result = asyncio.run(mcp_server.verify_snippet(fail_src))
    assert result["success"] is False
    assert any("postcondition" in d["code"] for d in result["diagnostics"])


def test_flush_cache_and_cancel_are_callable(service):
    mcp_server._service = service
    assert mcp_server.flush_cache() == {"flushed": True}
    cancelled = mcp_server.cancel()
    assert cancelled["cancelled"] is True


def test_options_to_kwargs_maps_and_filters():
    from nagini_translation.service import options_to_kwargs
    kw = options_to_kwargs({"verifier": "carbon", "intBitopsSize": 16,
                            "z3Path": None, "unknownKey": 1})
    assert kw == {"verifier_backend": "carbon", "int_bitops_size": 16}
    assert options_to_kwargs(None) == {}


def test_configure_switches_backend_and_service_stays_usable(service, pass_src):
    mcp_server._service = service
    try:
        assert mcp_server.configure({"verifier": "carbon"})["verifier"] == "carbon"
        assert mcp_server.configure({"verifier": "silicon"})["verifier"] == "silicon"
    finally:
        # Restore the shared session service for other tests.
        service.reconfigure(verifier_backend="silicon")
    # Verification still works after reconfiguration.
    result = asyncio.run(mcp_server.verify_snippet(pass_src))
    assert result["success"] is True


def test_configure_ignores_unknown_and_null_options(service):
    mcp_server._service = service
    effective = mcp_server.configure({"unknownKey": 1, "z3Path": None})
    # Returns the effective configuration without error; nothing changed.
    assert effective["verifier"] == "silicon"


def test_configure_reload_option_then_verify(service, pass_file, fail_file):
    # A reload-triggering option via the configure tool, then verification still
    # produces correct results.
    mcp_server._service = service
    original = service.current_options()
    try:
        effective = mcp_server.configure({"intBitopsSize": 16})
        assert effective["intBitopsSize"] == 16
        assert asyncio.run(mcp_server.verify_file(pass_file))["success"] is True
        assert asyncio.run(mcp_server.verify_file(fail_file))["success"] is False
    finally:
        service.reconfigure(int_bitops_size=original["intBitopsSize"])


_TOPLEVEL_ASSERT_SRC = (
    "from nagini_contracts.contracts import *\n\nassert False\n"
)
_BRANCH_ERROR_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def f(x: int) -> None:\n    if x > 0:\n        assert False\n"
)


def test_verify_ignore_global_via_tool(service):
    mcp_server._service = service
    # Top-level statements verified by default -> the false assert fails.
    assert asyncio.run(mcp_server.verify_snippet(_TOPLEVEL_ASSERT_SRC))["success"] is False
    # ignore_global param skips them -> verifies.
    assert asyncio.run(
        mcp_server.verify_snippet(_TOPLEVEL_ASSERT_SRC, ignore_global=True))["success"] is True


_MUST_TERMINATE_BAD_SRC = (
    "from nagini_contracts.contracts import *\n"
    "from nagini_contracts.obligations import MustTerminate\n\n"
    "def rec(n: int) -> int:\n    Requires(MustTerminate(1))\n    return rec(n)\n"
)


def test_verify_viper_args_and_write_viper_via_tool(service, tmp_path, pass_src):
    mcp_server._service = service
    out = tmp_path / "snippet.vpr"
    result = asyncio.run(mcp_server.verify_snippet(
        pass_src, viper_args=["--timeout=300"], write_viper_to_file=str(out)))
    assert result["success"] is True
    assert "method" in out.read_text()


def test_verify_obligations_override_via_tool(service):
    mcp_server._service = service
    assert asyncio.run(mcp_server.verify_snippet(
        _MUST_TERMINATE_BAD_SRC, obligations="ignore"))["success"] is True
    assert asyncio.run(mcp_server.verify_snippet(
        _MUST_TERMINATE_BAD_SRC))["success"] is False


def test_configure_disable_branch_conditions_via_tool(service):
    mcp_server._service = service
    original = service.current_options()
    try:
        mcp_server.configure({"disableBranchConditions": False})
        on = asyncio.run(mcp_server.verify_snippet(_BRANCH_ERROR_SRC))
        assert on["success"] is False
        assert any(d["branchConditions"] for d in on["diagnostics"])

        mcp_server.configure({"disableBranchConditions": True})
        off = asyncio.run(mcp_server.verify_snippet(_BRANCH_ERROR_SRC))
        assert off["success"] is False
        assert all(not d["branchConditions"] for d in off["diagnostics"])
    finally:
        service.reconfigure(
            disable_branch_conditions=original["disableBranchConditions"])
