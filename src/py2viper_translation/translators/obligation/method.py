"""Obligation translator in methods."""


from typing import List

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.typedefs import (
    Method,
    Stmt,
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
from py2viper_translation.translators.obligation.types.must_terminate import (
    MustTerminateObligationInstance,
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

    def _create_must_terminate_use(
            self, obligation_instance: MustTerminateObligationInstance,
            ctx: Context) -> expr.InhaleExhale:
        return obligation_instance.get_use_method(ctx)

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
