"""``MustTerminate`` obligation implementation.

Optimization
============

Observations:

1.  Handling ``MustTerminate`` significantly slows down the verifier (in
    ``example1`` test, Carbon slows down about 5 times).
2.  Most methods are either always terminating (have ``MustTerminate``
    in their precondition), or non-terminating (have no
    ``MustTerminate`` in their precondition).

Idea: detect three cases (always terminating, non-terminating, unknown)
and try to optimize encoding.

Usually there are many more method calls compared to loops. Therefore,
optimize only method calls.

The context is either a loop or a method that directly surrounds the
method call. If the context is:

1.  ``always_terminating`` and the callee is:

    1.  ``always_terminating``: check that measure is positive and
        decreases;
    2.  ``potentially_non_terminating``: invalid program error.
    3.  ``unknown_termination``: use non-optimized encoding.

2.  ``potentially_non_terminating`` and the callee is

    1.  ``always_terminating``: check that measure is positive and
        decreases;
    2.  ``potentially_non_terminating``: just do the context leak check;
    3.  ``unknown_termination``: use non-optimized encoding.

3.  ``unknown_termination`` and the callee is

    1.  ``always_terminating``: check that measure is positive and
        decreases;
    2.  ``potentially_non_terminating``: do the context leak check and
        check that ``perm(MustTerminate) == none``.
    3.  ``unknown_termination``: use non-optimized encoding.

Optimizations for method definition:

1.  If the method is ``always_terminating``, then replace
    ``MustTerminate`` predicate exhale with decreased measure check.
2.  If the method is ``always_terminating``, then remove the context
    leak check.
3.  If the method is ``potentially_non_terminating``, then make
    the caller context leak check unguarded.

Optimization for method call encoding:

1.  If the callee is not ``unknown_termination``, drop explicit
    ``MustTerminate`` check and all variable assignments, inhales, and
    exhales related to it. In addition:

    1.  If surrounding context is ``always_terminating`` and callee is
        ``potentially_non_terminating``, report an invalid program
        error.
        TODO: Check the case when calling a non-terminating method
        inside a terminating loop defined in a non-terminating method.
    2.  If surrounding context is ``unknown_termination`` add callee is
        ``potentially_non_terminating`` add an explicit check that
        callee is not required to terminate.

.. todo::

    Rewrite this thing as a table for better readability.
"""


import ast

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from py2viper_translation.lib import silver_nodes as sil
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules, rules
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


def _create_predicate_access(cthread: PythonVar) -> sil.PredicateAccess:
    """Create a predicate access expression."""
    return sil.PredicateAccess(_PREDICATE_NAME, sil.RefVar(cthread))


class TerminationGuarantee(Enum):
    """What guarantees a method provides about its termination."""

    always_terminating = 1
    """The method is always terminating.

    That is:

    +   method precondition has exactly one ``MustTerminate`` and it is
        unguarded, or
    +   method is axiomatized as terminating by annotation in
        ``preamble.index``.
    """

    potentially_non_terminating = 2
    """The method provides no termination guarantees.

    That is:

    +   method precondition has no ``MustTerminate``, or
    +   method is axiomatized as non-terminating in ``preamble.index``.
    """

    unknown_termination = 3
    """Statically unknown termination.

    All cases not-covered by ``always_terminating`` and
    ``potentially_non_terminating``.
    """


class MustTerminateObligationInstance(
        InexhaleObligationInstanceMixin, ObligationInstance):
    """Class representing instance of ``MustTerminate`` obligation."""

    def __init__(
            self, obligation: 'MustTerminateObligation', node: ast.expr,
            measure: ast.expr, target: PythonVar) -> None:
        super().__init__(obligation, node)
        self._measure = measure
        self._target = target

    def _get_inexhale(
            self, is_method: bool, ctx: Context) -> ObligationInhaleExhale:
        if is_method:
            obligation_info = ctx.actual_function.obligation_info
            if (obligation_info.get_termination_guarantee() is
                    TerminationGuarantee.always_terminating):
                return ObligationInhaleExhale(
                    _create_predicate_access(self._target),
                    max_one_inhale=False,   # We have only one MustTerminate.
                    exhale_only_check_measure=True)
        return ObligationInhaleExhale(
            _create_predicate_access(self._target),
            max_one_inhale=True)

    def get_use_method(
            self, ctx: Context) -> List[Tuple[sil.Expression, Rules]]:
        exprs = super().get_use_method(ctx)
        assert len(exprs) == 1
        return [(exprs[0][0], rules.OBLIGATION_MUST_TERMINATE_NOT_TAKEN)]

    def is_fresh(self) -> bool:
        return False    # MustTerminate is never fresh.

    def get_measure(self) -> sil.IntExpression:
        return sil.PythonIntExpression(self._measure)

    def get_target(self) -> sil.RefExpression:
        return sil.RefVar(self._target)


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
            self, cthread: PythonVar) -> sil.PredicateAccess:
        """Create a predicate access expression."""
        return _create_predicate_access(cthread)

    def is_interface_method_terminating(
            self, interface_dict: Dict[str, Any]) -> bool:
        """Check if interface method is annotated as terminating or not."""
        return (_OBLIGATION_NAME in interface_dict and
                interface_dict[_OBLIGATION_NAME])

    def generate_axiomatized_preconditions(
            self, obligation_info: 'PythonMethodObligationInfo',
            interface_dict: Dict[str, Any]) -> List[sil.BoolExpression]:
        """Add ``MustTerminate(1)`` to axiomatic method precondition."""
        if self.is_interface_method_terminating(interface_dict):
            cthread = sil.RefVar(obligation_info.current_thread_var)
            check = obligation_info.caller_measure_map.check(
                cthread, sil.RawIntExpression(1))
            return [check]
        else:
            return []

    def create_leak_check(self, var_name: str) -> List[sil.BoolExpression]:
        return [self._create_predicate_for_perm(_PREDICATE_NAME, var_name)]
