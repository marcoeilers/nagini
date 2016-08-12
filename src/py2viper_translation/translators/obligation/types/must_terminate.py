"""``MustTerminate`` obligation implementation."""


import ast

from typing import Any, Dict, List, Optional

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from py2viper_translation.translators.obligation.inexhale import (
    InexhaleObligationInstanceMixin,
    ObligationInhaleExhale,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
    Obligation,
)


_OBLIGATION_NAME = 'MustTerminate'
_PREDICATE_NAME = _OBLIGATION_NAME


def _create_predicate_access(cthread: PythonVar) -> expr.PredicateAccess:
    """Create a predicate access expression."""
    return expr.PredicateAccess(_PREDICATE_NAME, expr.VarRef(cthread))


def _create_method_exhale(
        obligation_info: 'PythonMethodObligationInfo',
        measure: expr.IntExpression) -> expr.Exhale:
    """Create ``MustTerminate`` exhale to be mentioned in precondition."""
    cthread = obligation_info.current_thread_var
    predicate = _create_predicate_access(cthread)
    check = obligation_info.caller_measure_map.check(
        expr.VarRef(cthread), measure)
    return expr.Implies(check, expr.Acc(predicate))


class MustTerminateObligationInstance(
        InexhaleObligationInstanceMixin, ObligationInstance):
    """Class representing instance of ``MustTerminate`` obligation."""

    def __init__(
            self, obligation: 'MustTerminateObligation', node: ast.expr,
            measure: ast.expr, target: PythonVar) -> None:
        super().__init__(obligation, node)
        self._measure = measure
        self._target = target

    def _get_inexhale(self) -> ObligationInhaleExhale:
        return ObligationInhaleExhale(
            _create_predicate_access(self._target),
            max_one_inhale=True)

    def is_fresh(self) -> bool:
        return False    # MustTerminate is never fresh.

    def get_measure(self) -> expr.IntExpression:
        return expr.PythonIntExpression(self._measure)

    def get_target(self) -> expr.RefExpression:
        return expr.VarRef(self._target)


class MustTerminateObligation(Obligation):
    """Class representing ``MustTerminate`` obligation."""

    def __init__(self) -> None:
        super().__init__([_PREDICATE_NAME], [])

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

    def create_predicate_access(
            self, cthread: PythonVar) -> expr.PredicateAccess:
        """Create a predicate access expression."""
        return _create_predicate_access(cthread)

    def is_interface_method_terminating(
            self, interface_dict: Dict[str, Any]) -> bool:
        """Check if interface method is annotated as terminating or not."""
        return (_OBLIGATION_NAME in interface_dict and
                interface_dict[_OBLIGATION_NAME])

    def generate_axiomatized_preconditions(
            self, obligation_info: 'PythonMethodObligationInfo',
            interface_dict: Dict[str, Any]) -> List[expr.BoolExpression]:
        """Add ``MustTerminate(1)`` to axiomatic method precondition."""
        if self.is_interface_method_terminating(interface_dict):
            exhale = _create_method_exhale(
                obligation_info, expr.RawIntExpression(1))
            return [exhale]
        else:
            return []

    def create_leak_check(self, var_name: str) -> List[expr.BoolExpression]:
        return [self._create_predicate_for_perm(_PREDICATE_NAME, var_name)]
