"""Obligation translator in methods."""


import ast

from typing import List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.typedefs import (
    Method,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.translators.obligation.common import (
    CommonObligationTranslator,
)
from py2viper_translation.translators.obligation.method_node import (
    ObligationMethod,
    ObligationsMethodNodeConstructor,
)
from py2viper_translation.translators.obligation.method_call_node import (
    ObligationMethodCall,
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
            self, ctx, name, original_args, returns, pres, posts,
            local_vars, body, position, info,
            method=None) -> Method:
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
            self, ctx, methodname, original_args, targets, position,
            info, target_method=None, target_node=None) -> List[Stmt]:
        """Construct a method call AST node with obligation stuff."""
        obligation_method_call = ObligationMethodCall(
            methodname, original_args, targets)
        constructor = ObligationsMethodCallNodeConstructor(
            obligation_method_call, position, info, self, ctx,
            self._obligation_manager, target_method, target_node)
        constructor.construct_call()
        return constructor.get_statements()
