"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.typedefs import Function, Method, Stmt
from nagini_translation.lib.program_nodes import PythonMethod, PythonModule
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.method import MethodTranslator

from typing import List

class ExtendedASTMethodTranslator(MethodTranslator):
    """
    Extended AST version of method translator.
    """

    def get_error_var(self, stmt: ast.AST, ctx: Context) -> 'silver.ast.LocalVarRef':
        return ctx.current_function.error_var.ref()

    def _method_body_postamble(self, method: PythonMethod, ctx: Context) -> List[Stmt]:
        # With extended AST we don't need goto end or catch blocks.
        return []

    def _create_method_epilog(self, method: PythonMethod, ctx: Context) -> List[Stmt]:
        # With the extended AST we don't need a label at the end of the method.
        # Check that no undeclared exceptions are raised. (but not for main method)
        if not method.declared_exceptions:
            no_info = self.no_info(ctx)
            error_string = '"method raises no exceptions"'
            error_pos = self.to_position(method.node, ctx, error_string)
            assert_no_err = self.viper.AssertNoException(error_pos, no_info)
            return [assert_no_err]
        return []

    def translate_method(self, method: PythonMethod, ctx: Context) -> Method:
        self.viper.ctx = ctx
        self.viper.type_factory = self.type_factory
        if method.all_low:
            self.viper.all_low_methods.add(method.sil_name)
        elif method.preserves_low:
            self.viper.preserves_low_methods.add(method.sil_name)
        return super().translate_method(method, ctx)

    # def translate_function(self, func: PythonMethod, ctx: Context) -> Function:
    #     if func.cls and func.name == '__eq__':
    #         self.viper.equality_comp_functions.add(func.sil_name)
    #     return super().translate_function(func, ctx)
