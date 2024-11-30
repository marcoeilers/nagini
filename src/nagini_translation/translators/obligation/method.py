"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Obligation translator in methods."""


import ast

from typing import List

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Method,
    Stmt,
    Position,
    VarDecl,
)
from nagini_translation.translators.obligation.common import (
    CommonObligationTranslator,
)
from nagini_translation.translators.obligation.fork import (
    ObligationMethodForkConstructor,
)
from nagini_translation.translators.obligation.method_node import (
    ObligationMethod,
    ObligationMethodNodeConstructor,
)
from nagini_translation.translators.obligation.method_call_node import (
    ObligationMethodCall,
    ObligationMethodCallNodeConstructor,
)
from nagini_translation.translators.obligation.types.base import (
    ObligationInstance,
)
from nagini_translation.translators.obligation.obligation_info import (
    BaseObligationInfo,
)
from nagini_translation.translators.obligation.utils import (
    find_method_by_sil_name,
)


class MethodObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in methods."""

    def _get_obligation_info(self, ctx: Context) -> BaseObligationInfo:
        return ctx.actual_function.obligation_info

    def _create_obligation_instance_use(
            self, obligation_instance: ObligationInstance,
            ctx: Context) -> sil.InhaleExhale:
        return obligation_instance.get_use_method(ctx)

    def create_method_node(     # pylint: disable=too-many-arguments,too-many-locals
            self, ctx: Context, name: str,
            original_args: List[VarDecl], returns: List[VarDecl],
            pres: List[Expr], posts: List[Expr],
            local_vars: List[VarDecl], body: List[Stmt],
            position: Position, info: Info,
            method: PythonMethod = None,
            overriding_check: bool = False) -> Method:
        """Construct method AST node with additional obligation stuff."""
        if method is None:
            method = find_method_by_sil_name(ctx, name)
        if method is None:
            # Assume that this is a method that is never called from
            # Python and, as a result, does not need obligation stuff.
            return self.viper.Method(
                name, original_args, returns, pres, posts, local_vars, body,
                position, info)

        assert (ctx.current_function is None or
                ctx.current_function == method)
        old_method = ctx.current_function
        ctx.current_function = method

        obligation_method = ObligationMethod(
            name, original_args, returns, pres, posts, local_vars, body)
        constructor = ObligationMethodNodeConstructor(
            obligation_method, method, self, ctx, self._obligation_manager,
            position, info, overriding_check)
        constructor.add_obligations()
        node = constructor.construct_node()

        ctx.current_function = old_method
        return node

    def create_method_call_node(
            self, ctx: Context, method_name: str, original_args: List[Expr],
            targets: List[Expr], position: Position, info: Info,
            target_method: PythonMethod = None,
            target_node: ast.Call = None) -> List[Stmt]:
        """Construct a method call AST node with obligation stuff."""
        obligation_method_call = ObligationMethodCall(
            method_name, original_args, targets)
        constructor = ObligationMethodCallNodeConstructor(
            obligation_method_call, position, info, self, ctx,
            self._obligation_manager, target_method, target_node)
        constructor.construct_call()
        return constructor.get_statements()

    def create_method_fork(self, ctx: Context, targets, thread: Expr,
                           position: Position, info: Info,
                           target_node: ast.Call=None) -> List[Stmt]:
        constructor = ObligationMethodForkConstructor(targets, thread, position, info,
                                                      self, ctx, self._obligation_manager,
                                                      target_node)
        constructor.construct_fork()
        return constructor.get_statements()
