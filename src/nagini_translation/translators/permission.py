"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator


class PermTranslator(CommonTranslator):

    def translate_perm(self, node: ast.AST, ctx: Context) -> Expr:
        """
        Generic visitor function for translating a permission amount
        """
        method = 'translate_perm_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_perm_Num(self, node: ast.Num, ctx: Context) -> Expr:
        if node.n == 1:
            return self.viper.FullPerm(self.to_position(node, ctx),
                                       self.no_info(ctx))
        raise UnsupportedException(node)

    def translate_perm_BinOp(self, node: ast.BinOp, ctx: Context) -> Expr:
        if isinstance(node.op, ast.Div):
            left_stmt, left = self.translate_expr(node.left, ctx,
                                                  self.viper.Int)
            right_stmt, right = self.translate_expr(node.right, ctx,
                                                    self.viper.Int)
            if left_stmt or right_stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return self.viper.FractionalPerm(left, right,
                                             self.to_position(node, ctx),
                                             self.no_info(ctx))
        raise UnsupportedException(node)