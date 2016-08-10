"""``MustInvoke`` obligation implementation."""


import ast

from typing import Any, Dict, List, Optional

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.translators.obligation.inexhale import (
    InexhaleObligationInstanceMixin,
    ObligationInhaleExhale,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
    Obligation,
)


_OBLIGATION_NAME = 'MustInvoke'
_BOUNDED_PREDICATE_NAME = _OBLIGATION_NAME + 'Bounded'
_UNBOUNDED_PREDICATE_NAME = _OBLIGATION_NAME + 'Unbounded'
_CREDIT_PREDICATE_NAME = _OBLIGATION_NAME + 'Credit'


class MustInvokeObligationInstance(
        InexhaleObligationInstanceMixin, ObligationInstance):
    """Class representing instance of ``MustInvoke`` obligation."""

    def __init__(
            self, obligation: 'MustInvokeObligation', node: ast.expr,
            measure: Optional[ast.expr], target: ast.expr) -> None:
        super().__init__(obligation, node)
        self._measure = measure
        self._target = target

    def _get_inexhale(self) -> ObligationInhaleExhale:
        return ObligationInhaleExhale(
            expr.PredicateAccess(_BOUNDED_PREDICATE_NAME, self.get_target()),
            expr.PredicateAccess(_UNBOUNDED_PREDICATE_NAME, self.get_target()),
            expr.PredicateAccess(_CREDIT_PREDICATE_NAME, self.get_target()))

    def is_fresh(self) -> bool:
        return self._measure is None

    def get_measure(self) -> expr.IntExpression:
        assert not self.is_fresh()
        return expr.PythonIntExpression(self._measure)

    def get_target(self) -> expr.RefExpression:
        return expr.PythonRefExpression(self._target)


class MustInvokeObligation(Obligation):
    """Class representing ``MustInvoke`` obligation."""

    def __init__(self) -> None:
        super().__init__([
            _BOUNDED_PREDICATE_NAME,
            _UNBOUNDED_PREDICATE_NAME,
            _CREDIT_PREDICATE_NAME], [])

    def identifier(self) -> str:
        return _OBLIGATION_NAME

    def check_node(
            self, node: ast.Call,
            obligation_info: 'PythonMethodObligationInfo',
            method: PythonMethod) -> Optional[MustInvokeObligationInstance]:
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

    def create_leak_check(self, var_name: str) -> List[expr.BoolExpression]:
        return [
            self._create_predicate_for_perm(
                _BOUNDED_PREDICATE_NAME, var_name),
            self._create_predicate_for_perm(
                _UNBOUNDED_PREDICATE_NAME, var_name),
        ]

    def create_ctoken_use(self, node: ast.Call) -> expr.Acc:
        """Create a ``ctoken`` use in contract."""
        target = expr.PythonRefExpression(node.args[0])
        return expr.Acc(expr.PredicateAccess(_CREDIT_PREDICATE_NAME, target))
