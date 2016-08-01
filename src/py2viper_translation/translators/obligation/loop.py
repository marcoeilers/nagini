"""Obligation translator in loops."""


import ast

from typing import List, Union

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    VarDecl,
)
from py2viper_translation.translators.obligation.common import (
    CommonObligationTranslator
)
from py2viper_translation.translators.obligation.loop_node import (
    ObligationLoop,
    ObligationLoopNodeConstructor,
)
from py2viper_translation.translators.obligation.types.must_terminate import (
    MustTerminateObligationInstance,
)
from py2viper_translation.translators.obligation.obligation_info import (
    BaseObligationInfo,
    PythonLoopObligationInfo,
)


class LoopObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in loops."""

    def enter_loop_translation(
            self, node: Union[ast.While, ast.For], ctx: Context,
            err_var: PythonVar = None) -> None:
        """Update context with info needed to translate loop."""
        info = PythonLoopObligationInfo(
            self._obligation_manager, node, self, ctx.actual_function,
            err_var)
        info.traverse_invariants()
        ctx.obligation_context.push_loop_info(info)

    def leave_loop_translation(self, ctx) -> None:
        """Remove loop translation info from context."""
        ctx.obligation_context.pop_loop_info()

    def _get_obligation_info(self, ctx: Context) -> BaseObligationInfo:
        return ctx.obligation_context.current_loop_info

    def _create_must_terminate_use(
            self, obligation_instance: MustTerminateObligationInstance,
            ctx: Context) -> expr.InhaleExhale:
        return obligation_instance.get_use_loop(ctx)

    def create_while_node(
            self, ctx: Context, cond: Expr,
            invariants: List[Expr],
            local_vars: List[VarDecl],
            body: List[Stmt], node: Union[ast.While, ast.For]) -> List[Stmt]:
        """Construct a while loop AST node with obligation stuff."""
        obligation_loop = ObligationLoop(cond, invariants, local_vars, body)
        constructor = ObligationLoopNodeConstructor(
            obligation_loop, node, self, ctx, self._obligation_manager)
        constructor.construct_loop()
        return constructor.get_statements()
