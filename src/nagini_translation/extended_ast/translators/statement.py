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
from nagini_translation.lib.program_nodes import PythonVar

class ExtendedASTStatementTranslator(StatementTranslator):
    """
    Extended AST Version of the StatementTranslator
    """
    def _translate_return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        if node.value:
            rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        else:
            rhs_stmt, rhs = [], self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if ctx.result_var:
            rvar = ctx.result_var.ref(node, ctx)
        else:
            rvar = None
        ret_stmt = self.viper.Return(rhs, rvar, pos, info)
        return rhs_stmt + [ret_stmt]

    def translate_stmt_Return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        return self._translate_return(node, ctx)

    def translate_stmt_Break(self, node: ast.Break, ctx: Context) -> List[Stmt]:
        return [self.viper.Break(self.to_position(node, ctx), self.no_info(ctx))]

    def translate_stmt_Continue(self, node: ast.Continue, ctx: Context) -> List[Stmt]:
        return [self.viper.Continue(self.to_position(node, ctx), self.no_info(ctx))]

    def _while_postamble(self, node: ast.While, post_label: str, ctx: Context) -> List[Stmt]:
        return self._set_result_none(ctx)

    def _translate_while_body(self, node: ast.While, ctx: Context, end_label: str) -> List[Stmt]:
        start, end = get_body_indices(node.body)
        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[start:end]])
        return body

    def translate_stmt_Try(self, node: ast.Try, ctx: Context) -> List[Stmt]:
        try_block = self._get_try_block(node, ctx)
        assert try_block
        body = flatten([self.translate_stmt(stmt, ctx) for stmt in node.body])
        else_block = []
        if try_block.else_block:
            else_block = flatten([self.translate_stmt(stmt, ctx)
                                    for stmt in try_block.else_block.body])
        finally_block = []
        if try_block.finally_block:
            finally_block = flatten([self.translate_stmt(stmt, ctx)
                                     for stmt in try_block.finally_block])
        catch_blocks = [] # type: 'silver.sif.SIFExceptionHandler'
        error_var = try_block.get_error_var(self.translator)
        if isinstance(error_var, PythonVar):
            error_var = error_var.ref()
        for handler in try_block.handlers:
            error_type_check = self.type_check(error_var, handler.exception,
                                               self.to_position(handler.node, ctx), ctx,
                                               inhale_exhale=False)
            handler_body = flatten([self.translate_stmt(stmt, ctx) for stmt in handler.body])
            handler_body_seqn = self.viper.Seqn(handler_body,
                                                self.no_position(ctx), self.no_info(ctx))
            catch_blocks.append(self.viper.SIFExceptionHandler(error_type_check, handler_body_seqn))
        return [self.viper.Try(self.viper.Seqn(body, self.no_position(ctx), self.no_info(ctx)),
                               catch_blocks,
                               self.viper.Seqn(else_block,
                                               self.no_position(ctx), self.no_info(ctx)),
                               self.viper.Seqn(finally_block,
                                               self.no_position(ctx), self.no_info(ctx)),
                               self.to_position(node, ctx), self.no_info(ctx))]

    def translate_stmt_Raise(self, node: ast.Raise, ctx: Context) -> List[Stmt]:
        stmts = self._translate_stmt_raise_create(node, ctx)
        return stmts[:-1] + [self.viper.Raise(stmts[-1],
                                              self.to_position(node, ctx), self.no_info(ctx))]
