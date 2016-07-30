"""Obligation translator in loops."""


import ast

from typing import List, Union

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
    VarDecl,
)
from py2viper_translation.lib.util import (
    UnsupportedException,
)
from py2viper_translation.translators.obligation.common import (
    CommonObligationTranslator
)


class LoopObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in loops."""

    def enter_loop_translation(
            self, node: Union[ast.While, ast.For], ctx: Context) -> None:
        """Update context with info needed to translate loop."""
        # TODO: This method is a stub.

    def leave_loop_translation(self, ctx: Context) -> None:
        """Remove loop translation info from context."""
        # TODO: This method is a stub.

    def translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``MustTerminate`` in method precondition."""
        raise UnsupportedException(node, 'Method is a stub.')

    def create_while_node(
            self, ctx: Context, cond: Expr,
            invariants: List[Expr],
            local_vars: List[VarDecl],
            body: Stmt, node: Union[ast.While, ast.For]) -> List[Stmt]:
        """Construct a while loop AST node with obligation stuff."""
        # TODO: This method is a stub.

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        statements = []

        body_block = self.translate_block(body,
                                          self.to_position(node, ctx),
                                          self.no_info(ctx))

        loop = self.viper.While(
            cond, invariants, local_vars, body_block, position, info)
        statements.append(loop)

        return statements
