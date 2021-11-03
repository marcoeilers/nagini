"""
Copyright (c) 2019 ETH Zurich
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

class SIFMethodTranslator(MethodTranslator):
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

    def translate_main_method(self, modules: List[PythonModule],
                              ctx: Context) -> List[Method]:
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)

        used_names = set()
        self.viper.used_names = used_names

        main = self._get_main_module(modules)
        main_method, locals, stmts = self._create_main_method_setup(modules, ctx)
        method_name = main_method.sil_name

        self.viper.used_names_sets[method_name] = used_names

        # Create an error variable
        error_var = self.create_method_error_var(ctx)
        main_method.error_var = error_var
        locals.append(error_var.decl)
        stmts.append(self.viper.LocalVarAssign(
            error_var.ref(),
            self.viper.NullLit(no_pos, no_info), no_pos, no_info))

        # Translate statements in main module. When an import statement is encountered,
        # the translation will include executing the statements in the imported module.
        for stmt in main.node.body:
            stmts.extend(self.translate_stmt(stmt, ctx))

        stmts += self._method_body_postamble(main_method, ctx)
        stmts += self._create_method_epilog(main_method, ctx)

        main_locals = [local.decl for local in main_method.get_locals()
                       if not local.name.startswith('lambda')]
        res = self.create_method_node(ctx, method_name, [], [], [], [],
                                      main_locals + locals, stmts, no_pos,
                                      no_info, method=ctx.current_function)
        ctx.current_function = None
        return main_method, res
