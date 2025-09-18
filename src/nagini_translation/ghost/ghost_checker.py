"""
Copyright (c) 2025 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import ast
from typing import List, Optional

from nagini_translation.lib.program_nodes import (PythonModule, PythonType, PythonMethod, PythonIOOperation)
from nagini_translation.lib.context import Context
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type


class GhostChecker:
    def __init__(self, modules: List[PythonModule]) -> None:
        self.modules = modules

    def check(self, ctx: Context):
        global_module = self.modules[0]
        main_module = self.modules[1]
        foo_class = main_module.classes['Foo']
        gint_class = main_module.classes['GInt']
        bar_method = main_module.methods['bar']

        bar_method_ast_node = bar_method.node  # get actual Python AST node for the function; could do the same for the classes
        ctx.current_function = bar_method  # update context
        self.check_FunctionDef(bar_method_ast_node, ctx)

    def check_FunctionDef(self, func: ast.FunctionDef, ctx: Context):
        stmts = func.body
        for stmt in stmts:  # iterate over statements in body
            if isinstance(stmt, ast.AnnAssign):  # for assignments with type annotations
                annotated_type = self.get_target(stmt.annotation, ctx)  # declared type
                rhs_type = self.get_type(stmt.value, ctx)  # right hand side type
                pass

    def get_target(self, node: ast.AST, ctx: Context) -> PythonModule:
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if ctx.current_class:
            containers.append(ctx.current_class)
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules(()))
        result = do_get_target(node, containers, container)
        return result

    def get_type(self, node: ast.AST, ctx: Context) -> Optional[PythonType]:
        """
        Returns the type of the expression represented by node as a PythonType,
        or None if the type is void.
        """
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if ctx.current_class:
            containers.append(ctx.current_class)
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules())
        return do_get_type(node, containers, container)