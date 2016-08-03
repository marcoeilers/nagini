"""``MustInvoke`` obligation implementation."""


import ast

from typing import Any, Dict, List, Optional

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
    Obligation,
)


_OBLIGATION_NAME = 'MustInvoke'
_BOUNDED_PREDICATE_NAME = _OBLIGATION_NAME + 'Bounded'
_UNBOUNDED_PREDICATE_NAME = _OBLIGATION_NAME + 'Unbounded'
_CREDIT_PREDICATE_NAME = _OBLIGATION_NAME + 'Credit'


class MustInvokeObligationInstance(ObligationInstance):
    """Class representing instance of ``MustInvoke`` obligation."""

    def __init__(
            self, obligation: 'MustTerminateObligation', node: ast.expr,
            measure: Optional[ast.expr], target: ast.expr) -> None:
        super().__init__(obligation, node)
        self._measure = measure
        self._target = target

    def is_fresh(self) -> bool:
        return self._measure is None

    def get_measure(self) -> expr.IntExpression:
        assert not self.is_fresh()
        return expr.PythonIntExpression(self._measure)

    def get_target(self) -> expr.RefExpression:
        return expr.PythonRefExpression(self._target)

    def get_use_method(self, ctx: Context) -> expr.Expression:
        bounded = expr.PredicateAccess(
            _BOUNDED_PREDICATE_NAME, self.get_target())
        unbounded = expr.PredicateAccess(
            _UNBOUNDED_PREDICATE_NAME, self.get_target())
        credit = expr.PredicateAccess(
            _CREDIT_PREDICATE_NAME, self.get_target())
        # TODO: Refactor code duplication.

        # Inhale part.
        if self.is_fresh():
            inhale = expr.Acc(unbounded)
        else:
            inhale = expr.Acc(bounded)

        # Exhale part.
        credit_exhale = expr.Acc(credit)
        unbounded_exhale = expr.BoolCondExp(
            expr.CurrentPerm(unbounded) > expr.NoPerm(),
            expr.Acc(unbounded),
            credit_exhale)
        if self.is_fresh():
            exhale = unbounded_exhale
        else:
            checks = [expr.CurrentPerm(bounded) > expr.NoPerm()]
            if not ctx.obligation_context.is_translating_posts:
                # Measure check is done only when calling a method.
                obligation_info = ctx.actual_function.obligation_info
                check = obligation_info.caller_measure_map.check(
                    self.get_target(), self.get_measure())
                checks.append(check)
            exhale = expr.BoolCondExp(
                expr.BigAnd(checks),
                expr.Acc(bounded),
                unbounded_exhale)

        return expr.InhaleExhale(inhale, exhale)

    def get_use_loop(self, ctx: Context) -> expr.Expression:
        bounded = expr.PredicateAccess(
            _BOUNDED_PREDICATE_NAME, self.get_target())
        unbounded = expr.PredicateAccess(
            _UNBOUNDED_PREDICATE_NAME, self.get_target())
        credit = expr.PredicateAccess(
            _CREDIT_PREDICATE_NAME, self.get_target())
        # TODO: Refactor code duplication.

        # Inhale part.
        inhale = expr.Acc(bounded)

        # Exhale part before loop.
        credit_exhale = expr.Acc(credit)
        unbounded_exhale = expr.BoolCondExp(
            expr.CurrentPerm(unbounded) > expr.NoPerm(),
            expr.Acc(unbounded),
            credit_exhale)
        exhale_before = expr.BoolCondExp(
            expr.CurrentPerm(bounded) > expr.NoPerm(),
            expr.Acc(bounded),
            unbounded_exhale)

        # Exhale part after loop body.
        credit_exhale = expr.Acc(credit)
        unbounded_exhale = expr.BoolCondExp(
            expr.CurrentPerm(unbounded) > expr.NoPerm(),
            expr.Acc(unbounded),
            credit_exhale)
        obligation_info = ctx.obligation_context.current_loop_info
        checks = [
            expr.CurrentPerm(bounded) > expr.NoPerm(),
            obligation_info.loop_measure_map.check(
                self.get_target(), self.get_measure())
        ]
        exhale_after = expr.BoolCondExp(
            expr.BigAnd(checks),
            expr.Acc(bounded),
            unbounded_exhale)

        # Exhale part together.
        exhale = expr.BoolCondExp(
            expr.BoolVar(obligation_info.loop_check_before_var),
            exhale_before,
            exhale_after)

        return expr.InhaleExhale(inhale, exhale)


class MustInvokeObligation(Obligation):
    """Class representing ``MustInvoke`` obligation."""

    def __init__(self) -> None:
        super().__init__([
            _BOUNDED_PREDICATE_NAME,
            _UNBOUNDED_PREDICATE_NAME,
            _CREDIT_PREDICATE_NAME])

    def identifier(self) -> str:
        return _OBLIGATION_NAME

    def check_node(
            self, node: ast.Call,
            obligation_info: 'PythonMethodObligationInfo',
            method: PythonMethod) -> Optional[MustInvokeObligationInstance]:
        # TODO: Add support for ctoken.
        if (isinstance(node.func, ast.Name) and
                node.func.id == 'token'):
            target = node.args[0]
            measure = node.args[1] if len(node.args) > 1 else None
            instance = MustInvokeObligationInstance(
                self, node, measure, target)
            return instance
        else:
            return None

    def generate_axiomatized_preconditions(
            self, obligation_info: 'PythonMethodObligationInfo',
            interface_dict: Dict[str, Any]) -> List[expr.BoolExpression]:
        return []
