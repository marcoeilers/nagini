"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
from typing import List

from nagini_translation.lib.typedefs import Stmt
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.statement import StatementTranslator
from nagini_translation.lib.util import flatten, get_body_indices


class ExtendedASTStatementTranslator(StatementTranslator):
    """
    Extended AST Version of the StatementTranslator
    """
    def _translate_return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if not ctx.result_var:
            rvar = self.viper.NullLit(pos, info)
        else:
            rvar = ctx.result_var.ref(node, ctx)
        ret_stmt = self.viper.Return(rhs, rvar, pos, info)
        return rhs_stmt + [ret_stmt]

    def translate_stmt_Return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        return self._translate_return(node, ctx)

    def translate_stmt_Break(self, node: ast.Break, ctx: Context) -> List[Stmt]:
        return [self.viper.Break(self.to_position(node, ctx), self.no_info(ctx))]

    def translate_stmt_Continue(self, node: ast.Continue, ctx: Context) -> List[Stmt]:
        return [self.viper.Continue(self.to_position(node, ctx), self.no_info(ctx))]

    def _while_postamble(self, node: ast.While, ctx: Context) -> List[Stmt]:
        return []

    def _translate_while_body(self, node: ast.While, ctx: Context, end_label: str) -> List[Stmt]:
        start, end = get_body_indices(node.body)
        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[start:end]])
        return body
