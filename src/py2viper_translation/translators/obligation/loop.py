"""Obligation translator in loops."""


import ast

from typing import List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    UnsupportedException,
)
from py2viper_translation.translators.obligation.common import (
    CommonObligationTranslator
)


class LoopObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in loops."""

    def enter_loop_translation(self, node, ctx) -> None:
        """Update context with info needed to translate loop."""
        # TODO: This method is a stub.

    def leave_loop_translation(self, ctx) -> None:
        """Remove loop translation info from context."""
        # TODO: This method is a stub.

    def translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``MustTerminate`` in method precondition."""
        raise UnsupportedException(node, 'Method is a stub.')

    def create_while_node(
            self, ctx, cond, invariants, local_vars, body, node) -> List[Stmt]:
        """Construct a while loop AST node with obligation stuff."""
        # TODO: This method is a stub.

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        statements = []

        body_block = self.translate_block(body, position, info)
        self._add_additional_invariants(invariants, ctx, position, info)

        loop = self.viper.While(
            cond, invariants, local_vars, body_block, position, info)
        statements.append(loop)

        return statements

    def _add_additional_invariants(
            self, invariants: List[Expr], ctx: Context,
            position: Position, info: Info) -> None:

        obligation_info = ctx.actual_function.obligation_info
        measure_map = obligation_info.method_measure_map
        permission = measure_map.get_contents_access()
        assertion = measure_map.get_contents_preserved_assertion()
        invariants[0:0] = [
            permission.translate(self, ctx, position, info),
            assertion.translate(self, ctx, position, info),
        ]
