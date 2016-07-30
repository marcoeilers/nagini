"""``MustTerminate`` obligation implementation."""


import ast

from typing import Optional

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
    Obligation,
)


_OBLIGATION_NAME = 'MustTerminate'
_PREDICATE_NAME = _OBLIGATION_NAME


class MustTerminateObligationInstance(ObligationInstance):
    """Class representing instance of ``MustTerminate`` obligation."""

    def __init__(
            self, obligation: 'MustTerminateObligation', node: ast.expr,
            measure: ast.expr, target: PythonVar) -> None:
        super().__init__(obligation, node)
        self._measure = measure
        self._target = target

    def is_fresh(self) -> bool:
        return False    # MustTerminate is never fresh.

    def get_measure(self) -> expr.IntExpression:
        return expr.PythonIntExpression(self._measure)

    def get_target(self) -> PythonVar:
        return self._target

    def get_use_method(self, ctx: Context) -> expr.Expression:
        """Get inhale exhale pair for use in method contract."""
        obligation_info = ctx.actual_function.obligation_info
        cthread = obligation_info.current_thread_var

        predicate = expr.Predicate(_PREDICATE_NAME, expr.VarRef(cthread))

        # Inhale part.
        inhale = expr.BigAnd([
            self.get_measure() > 0,
            expr.Implies(
                expr.CurrentPerm(predicate) == expr.NoPerm(),
                expr.Acc(predicate))
        ])

        # Exhale part.
        check = obligation_info.caller_measure_map.check(
            cthread, self.get_measure())
        exhale = expr.Implies(check, expr.Acc(predicate))

        return expr.InhaleExhale(inhale, exhale)


class MustTerminateObligation(Obligation):
    """Class representing ``MustTerminate`` obligation."""

    def __init__(self) -> None:
        super().__init__([_PREDICATE_NAME])

    def identifier(self) -> str:
        return _OBLIGATION_NAME

    def check_node(
            self, node: ast.Call,
            obligation_info: 'PythonMethodObligationInfo',
            method: PythonMethod) -> Optional[MustTerminateObligationInstance]:
        if (isinstance(node.func, ast.Name) and
                node.func.id == _OBLIGATION_NAME):
            measure = node.args[0]
            instance = MustTerminateObligationInstance(
                self, node, measure, obligation_info.current_thread_var)
            return instance
        else:
            return None

    def create_predicate_access(self, cthread: PythonVar) -> expr.Predicate:
        """Create a predicate access expression."""
        return expr.Predicate(_PREDICATE_NAME, expr.VarRef(cthread))
