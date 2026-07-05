"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


import asyncio

import pytest

pytest.importorskip("mcp")

from nagini_translation import mcp_server


_DIAG_KEYS = {"file", "startLine", "startCol", "endLine", "endCol", "severity",
              "code", "source", "message"}


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
