"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from typing import List, Tuple

from nagini_translation.translators.call import CallTranslator
from nagini_translation.translators.abstract import Context
from nagini_translation.lib.program_nodes import PythonMethod, PythonVar
from nagini_translation.lib.typedefs import Stmt

class SIFCallTranslator(CallTranslator):
    """
    Extended AST version of call translator.
    """

    def get_error_var(self, stmt: ast.AST, ctx: Context) -> 'silver.ast.LocalVarRef':
        return ctx.current_function.error_var.ref()

    def inline_method(self, method: PythonMethod, args: List[PythonVar],
                      result_var: PythonVar, error_var: PythonVar,
                      ctx: Context) -> Tuple[List[Stmt], 'silver.ast.Label']:
        stmts, _ = super().inline_method(method, args, result_var, error_var, ctx)
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        seqn = self.viper.Seqn(stmts, pos, info)
        return [self.viper.InlinedCall(seqn, pos, info)], None
