"""Code for constructing Silver while node with obligation stuff."""


import ast

from typing import List, Union

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    VarDecl,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.node_constructor import (
    StatementNodeConstructorBase,
)


class ObligationLoop:
    """Info for generating Silver ``While`` AST node."""

    def __init__(
            self, condition: Expr, invariants: List[Expr],
            local_vars: List[VarDecl], body: List[Stmt]) -> None:
        self.condition = condition
        self.invariants = invariants
        self.local_vars = local_vars
        self.body = body

    def prepend_invariants(self, invariants) -> None:
        """Prepend ``invariants`` to the invariants list."""
        self.invariants[0:0] = invariants


class ObligationLoopNodeConstructor(StatementNodeConstructorBase):
    """A class that creates a while loop node with obligation stuff."""

    def __init__(
            self, obligation_loop: ObligationLoop,
            node: Union[ast.While, ast.For],
            translator: 'AbstractTranslator', ctx: Context,
            obligation_manager: ObligationManager) -> None:
        position = translator.to_position(node, ctx)
        info = translator.no_info(ctx)
        super().__init__(
            translator, ctx, obligation_manager, position, info, node)
        self._obligation_loop = obligation_loop
        self._node = node

    def get_statements(self) -> List[Stmt]:
        """Get all generated statements."""
        return self._statements

    def construct_loop(self) -> None:
        """Construct statements to perform a loop."""
        self._add_method_measure_map_preserved_invariant()
        self._add_loop()
        # TODO: Implement.

    def _add_loop(self) -> None:
        """Add the actual loop node."""
        body_block = self._translator.translate_block(
            self._obligation_loop.body, self._position, self._info)
        loop = self._viper.While(
            self._obligation_loop.condition, self._obligation_loop.invariants,
            self._obligation_loop.local_vars, body_block,
            self._position, self._info)
        self._statements.append(loop)

    def _add_method_measure_map_preserved_invariant(self) -> None:
        """Add invariant that method measure map is not changed."""
        # TODO: Clean up obligation_info set up.
        obligation_info = self._ctx.actual_function.obligation_info
        measure_map = obligation_info.method_measure_map
        permission = measure_map.get_contents_access()
        assertion = measure_map.get_contents_preserved_assertion()
        self._obligation_loop.prepend_invariants([
            permission.translate(
                self._translator, self._ctx, self._position, self._info),
            assertion.translate(
                self._translator, self._ctx, self._position, self._info),
        ])
