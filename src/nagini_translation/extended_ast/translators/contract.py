"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.typedefs import StmtsAndExpr
from nagini_translation.lib.util import UnsupportedException, InvalidProgramException
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.contract import ContractTranslator


class ExtendedASTContractTranslator(ContractTranslator):
    """
    Extended AST version of the contract translator.
    """

    def translate_low(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Low() contract function.
        """
        if len(node.args) != 1:
            raise UnsupportedException(node, "Low() requires exactly one argument")
        stmts, expr = self.translate_expr(node.args[0], ctx)
        if stmts:
            raise InvalidProgramException(node, 'purity.violated')
        # determine if surrounding method is dynamically bound
        return [], self.viper.Low(expr, self.to_position(node, ctx),
                                  self.no_info(ctx))

    def translate_lowevent(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the LowEvent() contract function.
        """
        return [], self.viper.LowEvent(self.to_position(node, ctx), self.no_info(ctx))
