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


class ExtendedASTStatementTranslator(StatementTranslator):
    """
    Extended AST Version of the StatementTranslator
    """
    def _translate_return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        # if not ctx.result_var:
        #     null = self.viper.NullLit(pos, info)
        ret_stmt = self.viper.Return(rhs, ctx.result_var.ref(node, ctx), pos, info)
        return [ret_stmt]

    def translate_stmt_Return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        return self._translate_return(node, ctx)
