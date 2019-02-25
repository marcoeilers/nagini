"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
from typing import List

from nagini_translation.lib.program_nodes import PythonTryBlock, PythonVar
from nagini_translation.lib.typedefs import Stmt
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.expression import ExpressionTranslator


class SIFExpressionTranslator(ExpressionTranslator):
    """
    Extended AST Version of the ExpressionTranslator.
    """

    def create_exception_catchers(self, var: PythonVar,
                                  try_blocks: List[PythonTryBlock],
                                  call: ast.Call, ctx: Context) -> List[Stmt]:
        if isinstance(var, PythonVar):
            var = var.ref() # the error variable
        position = self.to_position(call, ctx)
        errnotnull = self.viper.NeCmp(var,
                                      self.viper.NullLit(self.no_position(ctx),
                                                         self.no_info(ctx)),
                                      position, self.no_info(ctx))
        raise_stmt = self.viper.Raise(None, self.no_position(ctx), self.no_info(ctx))
        errcheck = self.viper.If(errnotnull, raise_stmt, self.viper.Skip(),
                                 position, self.no_info(ctx))
        return [errcheck]
