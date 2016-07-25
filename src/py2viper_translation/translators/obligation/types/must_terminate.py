"""``MustTerminate`` obligation implementation."""


import ast

from typing import Optional

from py2viper_translation.lib.util import (
    UnsupportedException,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
    Obligation,
)


class MustTerminateObligationInstance(ObligationInstance):
    """Class representing instance of ``MustTerminate`` obligation."""

    def __init__(self, node: ast.expr, measure: ast.expr) -> None:
        super().__init__(node)
        self._measure = measure

    def is_fresh(self) -> bool:
        return False    # MustTerminate is never fresh.

    def get_measure(self) -> "IntegerExpression":
        raise UnsupportedException(None, 'Not implemented.')


class MustTerminateObligation(Obligation):
    """Class representing ``MustTerminate`` obligation."""

    OBLIGATION_NAME = 'MustTerminate'

    PREDICATE_NAME = OBLIGATION_NAME

    def __init__(self) -> None:
        super().__init__([self.PREDICATE_NAME])

    def identifier(self) -> str:
        return self.OBLIGATION_NAME

    def check_node(
            self,
            node: ast.Call) -> Optional[MustTerminateObligationInstance]:
        if (isinstance(node.func, ast.Name) and
                node.func.id == self.OBLIGATION_NAME):
            measure = node.args[0]
            instance = MustTerminateObligationInstance(node, measure)
            return instance
        else:
            return None
