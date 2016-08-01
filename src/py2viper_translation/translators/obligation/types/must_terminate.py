"""``MustTerminate`` obligation implementation."""


import ast

from typing import Any, Dict, List, Optional

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


def _create_predicate_access(cthread: PythonVar) -> expr.Predicate:
    """Create a predicate access expression."""
    return expr.Predicate(_PREDICATE_NAME, expr.VarRef(cthread))


def _create_method_exhale(
        obligation_info: 'PythonMethodObligationInfo',
        measure: expr.IntExpression) -> expr.Exhale:
    """Create ``MustTerminate`` exhale to be mentioned in precondition."""
    cthread = obligation_info.current_thread_var
    predicate = _create_predicate_access(cthread)
    check = obligation_info.caller_measure_map.check(cthread, measure)
    return expr.Implies(check, expr.Acc(predicate))


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

    def _create_predicate_access(self, ctx) -> expr.Predicate:
        obligation_info = ctx.actual_function.obligation_info
        cthread = obligation_info.current_thread_var
        return _create_predicate_access(cthread)

    def _create_permission_inhale(
            self, predicate: expr.Predicate) -> expr.BoolExpression:
        return expr.Implies(
            expr.CurrentPerm(predicate) == expr.NoPerm(),
            expr.Acc(predicate))

    def get_use_method(self, ctx: Context) -> expr.Expression:
        """Get inhale exhale pair for use in method contract."""
        predicate = self._create_predicate_access(ctx)

        # Inhale part.
        inhale = expr.BigAnd([
            self.get_measure() > 0,
            self._create_permission_inhale(predicate)
        ])

        # Exhale part.
        exhale = _create_method_exhale(
            ctx.actual_function.obligation_info,
            self.get_measure())

        return expr.InhaleExhale(inhale, exhale)

    def get_use_loop(self, ctx: Context) -> expr.Expression:
        """Get inhale exhale pair for use in loop invariant."""
        predicate = self._create_predicate_access(ctx)

        # Measures positive.
        loop_info = ctx.obligation_context.current_loop_info
        loop_condition = loop_info.construct_loop_condition()
        measures_positive = expr.Implies(
            loop_condition, self.get_measure() > 0)

        # Inhale part.
        inhale = self._create_permission_inhale(predicate)

        # Exhale part.
        exhale = expr.TrueLit()

        return expr.BigAnd([
            measures_positive,
            expr.InhaleExhale(inhale, exhale)])


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
        return _create_predicate_access(cthread)

    def generate_axiomatized_preconditions(
            self, obligation_info: 'PythonMethodObligationInfo',
            interface_dict: Dict[str, Any]) -> List[expr.BoolExpression]:
        """Add ``MustTerminate(1)`` to axiomatic method precondition."""
        if (_OBLIGATION_NAME in interface_dict and
                interface_dict[_OBLIGATION_NAME]):
            exhale = _create_method_exhale(
                obligation_info, expr.RawIntExpression(1))
            return [exhale]
        else:
            return []
