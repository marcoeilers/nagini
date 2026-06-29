"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""
Language Server Protocol frontend for Nagini.

Exposes the shared :class:`VerificationService` over LSP (stdio): live
diagnostics on open/save, a "Verify method" code lens, counterexample/contract
hover, progress notifications, and cancellation of superseded runs.
"""


import argparse
import ast
import asyncio
import logging
import os
import sys

from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Set

from lsprotocol import types as t
from pygls import uris
from pygls.lsp.server import LanguageServer

from nagini_translation.service import (
    add_service_arguments,
    Diagnostic,
    make_service,
    VerificationService,
)


VERIFY_METHOD_COMMAND = 'nagini.verifyMethod'


class NaginiLanguageServer(LanguageServer):

    def __init__(self):
        super().__init__('nagini-lsp', 'v0.1')
        self.service: Optional[VerificationService] = None
        self.counterexamples = True
        # Several documents can verify at once; the service serializes only the
        # fast translation step internally.
        self._executor = ThreadPoolExecutor(max_workers=4,
                                            thread_name_prefix='nagini-verify')
        self._last_diagnostics = {}  # uri -> List[Diagnostic]

    async def run_verification(self, uri: str, selected: Set[str] = None) -> None:
        if self.service is None:
            return
        path = uris.to_fs_path(uri)
        if path is None:
            return
        # Precisely supersede any in-flight run *of this document*; other
        # documents keep verifying concurrently. The job token is the URI.
        self.service.cancel(job_token=uri)
        self.window_log_message(t.LogMessageParams(
            type=t.MessageType.Info, message='Nagini: verifying {}...'.format(path)))
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor, self._verify_blocking, uri, path, selected)
        if result.cancelled:
            # Superseded by a newer run; keep the existing diagnostics.
            return
        self._last_diagnostics[uri] = result.diagnostics
        self.text_document_publish_diagnostics(t.PublishDiagnosticsParams(
            uri=uri,
            diagnostics=[_to_lsp_diagnostic(d, uri) for d in result.diagnostics]))
        summary = ('verification successful' if result.success
                   else 'verification failed ({} issue(s))'.format(len(result.diagnostics)))
        self.window_log_message(t.LogMessageParams(
            type=t.MessageType.Info,
            message='Nagini: {} in {:.1f}s'.format(summary, result.duration)))

    def _verify_blocking(self, uri, path, selected):
        return self.service.verify(path, selected=selected,
                                   counterexample=self.counterexamples, job_token=uri)


server = NaginiLanguageServer()


def _to_lsp_diagnostic(d: Diagnostic, uri: str) -> t.Diagnostic:
    # Nagini lines are 1-indexed; LSP lines are 0-indexed. Columns are 0-indexed
    # in both.
    start = t.Position(line=max(d.start_line - 1, 0), character=max(d.start_col, 0))
    end = t.Position(line=max(d.end_line - 1, 0), character=max(d.end_col, 0))
    message = d.message if not d.reason else '{} {}'.format(d.message, d.reason)
    related = None
    if d.reason_position is not None:
        rl, rc = d.reason_position
        related = [t.DiagnosticRelatedInformation(
            location=t.Location(uri=uri, range=t.Range(
                start=t.Position(line=max(rl - 1, 0), character=max(rc, 0)),
                end=t.Position(line=max(rl - 1, 0), character=max(rc, 0)))),
            message=d.reason or 'reason')]
    return t.Diagnostic(
        range=t.Range(start=start, end=end),
        message=message,
        severity=t.DiagnosticSeverity.Error,
        code=d.code,
        source=d.source,
        related_information=related)


def _functions(source: str):
    """Yield (qualified_name, FunctionDef) for every function in the source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield (prefix + child.name, child)
                yield from walk(child, prefix + child.name + '.')
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, prefix + child.name + '.')
    yield from walk(tree, '')


@server.feature(t.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: NaginiLanguageServer, params: t.DidOpenTextDocumentParams):
    await ls.run_verification(params.text_document.uri)


@server.feature(t.TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls: NaginiLanguageServer, params: t.DidSaveTextDocumentParams):
    await ls.run_verification(params.text_document.uri)


@server.feature(t.TEXT_DOCUMENT_CODE_LENS)
def code_lens(ls: NaginiLanguageServer, params: t.CodeLensParams) -> List[t.CodeLens]:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    lenses = []
    for name, node in _functions(doc.source):
        line = max(node.lineno - 1, 0)
        lenses.append(t.CodeLens(
            range=t.Range(start=t.Position(line=line, character=0),
                          end=t.Position(line=line, character=0)),
            command=t.Command(title='▶ Verify method', command=VERIFY_METHOD_COMMAND,
                              arguments=[params.text_document.uri, name])))
    return lenses


@server.command(VERIFY_METHOD_COMMAND)
async def verify_method(ls: NaginiLanguageServer, args):
    uri, name = args[0], args[1]
    await ls.run_verification(uri, selected={name})


@server.feature(t.TEXT_DOCUMENT_HOVER)
def hover(ls: NaginiLanguageServer, params: t.HoverParams) -> Optional[t.Hover]:
    uri = params.text_document.uri
    line = params.position.line  # 0-indexed
    # 1) Counterexample / branch conditions for a failing line.
    for d in ls._last_diagnostics.get(uri, []):
        if (d.start_line - 1) <= line <= (d.end_line - 1) and (d.counterexample or d.branch_conditions):
            parts = []
            if d.counterexample:
                parts.append('**Counterexample**\n```\n{}\n```'.format(d.counterexample))
            if d.branch_conditions:
                parts.append('**Branch conditions:** ' + ', '.join(d.branch_conditions))
            return t.Hover(contents=t.MarkupContent(
                kind=t.MarkupKind.Markdown, value='\n\n'.join(parts)))
    # 2) Contract of the function whose name is under the cursor (best-effort).
    contract = _contract_hover(ls, uri, params.position)
    if contract:
        return t.Hover(contents=t.MarkupContent(kind=t.MarkupKind.Markdown, value=contract))
    return None


_CONTRACT_FUNCS = ('Requires', 'Ensures', 'Decreases', 'Invariant')


def _contract_hover(ls, uri, position) -> Optional[str]:
    doc = ls.workspace.get_text_document(uri)
    source = doc.source
    lines = source.splitlines()
    if position.line >= len(lines):
        return None
    word = _word_at(lines[position.line], position.character)
    if not word:
        return None
    for name, node in _functions(source):
        if node.name != word:
            continue
        clauses = []
        for stmt in node.body:
            if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id in _CONTRACT_FUNCS):
                seg = ast.get_source_segment(source, stmt.value)
                if seg:
                    clauses.append(seg)
        if clauses:
            body = '\n'.join('- `{}`'.format(c) for c in clauses)
            return '**Contract of `{}`**\n\n{}'.format(name, body)
        return None
    return None


def _word_at(line: str, char: int) -> Optional[str]:
    if char > len(line):
        return None
    start = char
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] == '_'):
        start -= 1
    end = char
    while end < len(line) and (line[end].isalnum() or line[end] == '_'):
        end += 1
    word = line[start:end]
    return word or None


def main():
    parser = argparse.ArgumentParser(description='Nagini LSP server (stdio).')
    add_service_arguments(parser)
    parser.add_argument('--no-counterexamples', action='store_true',
                        help='do not compute counterexamples (faster)')
    parser.add_argument('--log', default='WARNING')
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.WARNING))
    server.counterexamples = not args.no_counterexamples
    server.service = make_service(args)
    try:
        server.start_io()
    finally:
        # ViperServer/Akka leaves non-daemon threads alive; shut down and force
        # exit so the process actually terminates when the client disconnects.
        try:
            server.service.shutdown()
        except Exception:
            logging.exception('Error shutting down service.')
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)


if __name__ == '__main__':
    main()
