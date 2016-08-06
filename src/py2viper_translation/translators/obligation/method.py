"""Obligation translator in methods."""


import ast

from typing import List

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Method,
    Stmt,
    Position,
    VarDecl,
)
from py2viper_translation.translators.obligation.common import (
    CommonObligationTranslator,
)
from py2viper_translation.translators.obligation.method_node import (
    ObligationMethod,
    ObligationMethodNodeConstructor,
)
from py2viper_translation.translators.obligation.method_call_node import (
    ObligationMethodCall,
    ObligationMethodCallNodeConstructor,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
)
from py2viper_translation.translators.obligation.obligation_info import (
    BaseObligationInfo,
)
from py2viper_translation.translators.obligation.utils import (
    find_method_by_sil_name,
)


class MethodObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in methods."""

    def _get_obligation_info(self, ctx: Context) -> BaseObligationInfo:
        return ctx.actual_function.obligation_info

    def _create_obligation_instance_use(
            self, obligation_instance: ObligationInstance,
            ctx: Context) -> expr.InhaleExhale:
        return obligation_instance.get_use_method(ctx)

    def create_method_node(     # pylint: disable=too-many-arguments
            self, ctx: Context, name: str,
            original_args: List[VarDecl], returns: List[VarDecl],
            pres: List[Expr], posts: List[Expr],
            local_vars: List[VarDecl], body: List[Stmt],
            position: Position, info: Info,
            method: PythonMethod = None,
            overriding: bool = False) -> Method:
        """Construct method AST node with additional obligation stuff."""
        if method is None:
            method = find_method_by_sil_name(ctx, name)
        if method is None:
            # Assume that this is a method that is never called from
            # Python and, as a result, does not need obligation stuff.
            return self.viper.Method(
                name, original_args, returns, pres, posts, local_vars, body,
                position, info)

        obligation_method = ObligationMethod(
            name, original_args, returns, pres, posts, local_vars, body)
        constructor = ObligationMethodNodeConstructor(
            obligation_method, method, self, ctx, self._obligation_manager,
            position, info, overriding)
        constructor.add_obligations()

        return constructor.construct_node()

    def create_method_call_node(
            self, ctx: Context, methodname: str, original_args: List[Expr],
            targets: List[Expr], position: Position, info: Info,
            target_method: PythonMethod = None,
            target_node: ast.Call = None) -> List[Stmt]:
        """Construct a method call AST node with obligation stuff."""
        obligation_method_call = ObligationMethodCall(
            methodname, original_args, targets)
        constructor = ObligationMethodCallNodeConstructor(
            obligation_method_call, position, info, self, ctx,
            self._obligation_manager, target_method, target_node)
        constructor.construct_call()
        return constructor.get_statements()
