"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


import asyncio

import pytest

pytest.importorskip("pygls")

from pygls import uris

from nagini_translation import lsp_server
from nagini_translation.service import Diagnostic


# -- pure unit tests (no JVM) ----------------------------------------------

def test_to_lsp_diagnostic_converts_to_zero_indexed_lines():
    d = Diagnostic(file="x.py", start_line=5, start_col=12, end_line=5,
                   end_col=24, message="msg", code="a:b", reason="r",
                   reason_position=(5, 12))
    ld = lsp_server._to_lsp_diagnostic(d, "file:///x.py")
    # Nagini lines are 1-indexed; LSP lines are 0-indexed. Columns stay.
    assert (ld.range.start.line, ld.range.start.character) == (4, 12)
    assert (ld.range.end.line, ld.range.end.character) == (4, 24)
    assert ld.code == "a:b"
    assert ld.source == "nagini"
    assert ld.related_information
    assert ld.related_information[0].location.range.start.line == 4


def test_functions_yields_qualified_names():
    src = ("class C:\n"
           "    def m(self) -> int:\n"
           "        return 1\n"
           "def f() -> int:\n"
           "    return 2\n")
    names = sorted(name for name, _ in lsp_server._functions(src))
    assert names == ["C.m", "f"]


def test_functions_tolerates_syntax_errors():
    assert list(lsp_server._functions("def (:::")) == []


def test_word_at_finds_identifier():
    assert lsp_server._word_at("    return foo_bar(x)", 13) == "foo_bar"
    assert lsp_server._word_at("", 0) is None


# -- integration tests (require the verification service) -------------------

def _verify_via_lsp(service, monkeypatch, uri):
    server = lsp_server.NaginiLanguageServer()
    server.service = service
    captured = []
    monkeypatch.setattr(server, "text_document_publish_diagnostics",
                        lambda params: captured.append(params))
    monkeypatch.setattr(server, "window_log_message", lambda *a, **k: None)
    asyncio.run(server.run_verification(uri))
    return captured


def test_failing_file_publishes_diagnostic(service, fail_file, monkeypatch):
    captured = _verify_via_lsp(service, monkeypatch, uris.from_fs_path(fail_file))
    assert len(captured) == 1
    diags = captured[0].diagnostics
    assert len(diags) == 1
    assert "postcondition" in diags[0].code
    # The diagnostic points at the postcondition (line 5, 1-indexed -> 4).
    assert diags[0].range.start.line == 4


def test_passing_file_publishes_no_diagnostics(service, pass_file, monkeypatch):
    captured = _verify_via_lsp(service, monkeypatch, uris.from_fs_path(pass_file))
    assert len(captured) == 1
    assert captured[0].diagnostics == []


def test_code_lens_offered_per_function(service, fail_file, monkeypatch):
    # _functions backs the code lens provider; verify it sees the method.
    with open(fail_file) as f:
        names = [name for name, _ in lsp_server._functions(f.read())]
    assert "add" in names
