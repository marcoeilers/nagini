"""Obligation translator in methods."""


import ast

from typing import List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
    Stmt,
    StmtsAndExpr,
    VarDecl,
)
from py2viper_translation.translators.obligation.common import (
    CommonObligationTranslator,
)
from py2viper_translation.translators.obligation.method_node import (
    ObligationMethod,
    ObligationsMethodNodeConstructor,
)
from py2viper_translation.translators.obligation.method_call_node import (
    ObligationsMethodCallNodeConstructor,
)
from py2viper_translation.translators.obligation.types import (
    must_terminate,
)
from py2viper_translation.translators.obligation.utils import (
    find_method_by_sil_name,
)


class MethodObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in methods."""

    def translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``MustTerminate`` in loop invariant."""
        obligation_info = ctx.actual_function.obligation_info
        guarded_obligation_instance = obligation_info.get_instance(node)
        obligation_instance = guarded_obligation_instance.obligation_instance
        assert isinstance(obligation_instance,
                          must_terminate.MustTerminateObligationInstance)

        inhale_exhale = obligation_instance.get_use_method(ctx)

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        expr = inhale_exhale.translate(self, ctx, position, info)
        return ([], expr)

    def create_method_node(
            self, ctx: Context, name: str,
            original_args: List[VarDecl], returns: List[VarDecl],
            pres: List[Expr], posts: List[Expr],
            local_vars: List[VarDecl], body: List[Stmt],
            position: Position, info: Info,
            method: PythonMethod = None) -> List[Stmt]:
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
        constructor = ObligationsMethodNodeConstructor(
            obligation_method, method, self, ctx, position, info)
        constructor.add_obligations()

        return constructor.construct_node()

    def create_method_call_node(
            self, ctx: Context, methodname: str, original_args: List[Expr],
            targets: List[Expr], position: Position, info: Info,
            target_method: PythonMethod = None,
            target_node: ast.Call = None) -> List[Stmt]:
        """Construct a method call AST node with obligation stuff."""
        constructor = ObligationsMethodCallNodeConstructor(
            methodname, original_args, targets, position, info, self, ctx,
            target_method, target_node)
        constructor.construct_call()
        return constructor.get_statements()
