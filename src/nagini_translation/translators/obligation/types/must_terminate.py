"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

# pragma pylint: disable=wrong-spelling-in-docstring

r"""``MustTerminate`` obligation implementation.

The reasons why we do not follow original paper [Obligations]_ directly
are:

1.  We want to reuse Viper constructs as much as possible, which means
    that we would like to avoid replacing a method call with an exhale
    inhale pair.
2.  We do not want to have an additional argument, which indicates if
    the caller has an obligation to terminate or not.
3.  We want to have a consistent encoding for loops and methods.

``MustTerminate`` obligation encoding implemented in Chalice2Silver
([C2SObligations]_) turned out to be unsound (see issue `84
<https://bitbucket.org/viperproject/chalice2silver/issues/84/>`_). The
problem is that the callee's promise to terminate is checked after the
method call. If callee's postcondition is ``False`` (a possible
postcondition for non-terminating method), the check trivially passes.
Nagini therefore uses a different encoding.

``MustTerminate`` in Contracts
==============================

Like in [C2SObligations]_, ``MustTerminate`` mentioned in method
preconditions and loop invariants are translated into inhale/exhale
pair:

+   Unlike in [C2SObligations]_, we do not need to guarantee that we
    have at most full permission to ``MustTerminate``. We therefore just
    inhale a full permission to ``MustTerminate`` each time.
+   We do not exhale ``MustTerminate`` obligation (unlike in
    [C2SObligations]_), we only check that measure is strictly positive.

Promise to Terminate
====================

As described in the previous section, we do not exhale
``MustTerminate``. We therefore need a different mechanism for detecting
if a method call / loop promised to terminate. The idea is to generate a
boolean expression that is ``True`` iff method call / loop promised to
terminate. That is if there is at least one ``MustTerminate`` whose
guarding condition and measure check evaluates to ``True``. More
precisely, we define termination condition as:

.. math::

    tcond := \lor \left\{%
        guard(o) \land measure_check(o) :
        o \in \text{MustTerminate obligations in contract}
    \right\}

We also define a version that ignores measures:

.. math::

    tcond_no_measure := \lor \left\{%
        guard(o) :
        o \in \text{MustTerminate obligations in contract}
    \right\}

.. note::

    In subsequent sections :math:`tcond` and :math:`tcond_no_measure`
    are used as a macros.

:math:`tcond` and :math:`tcond_no_measure` implementation is provided by
:py:class:`BaseObligationInfo.create_termination_check`.

Method Encoding
===============

At the end of each method precondition, we add a leak check guarded by
:math:`tcond`. The whole expression added to the precondition in the
optimized form:

.. math::

    tcond \lor
    (perm(cthread) == none \land \text{leak check for other obligation types})

:math:`perm(cthread) == none` is an optimized form of the leak check for
``MustTerminate`` obligation. Note that in our encoding like in
[C2SObligations]_, leak check does not include ``MustTerminate``
obligation type.

.. note::

    Unlike in [C2SObligations]_, we do not emit any additional code on
    the caller side.

.. note::

    For axiomatic methods (the ones that are defined in
    ``preamble.index``) we add additional precondition:

    1.  If method is marked as terminating, we add a check that caller
        termination measure is bigger than 1:

        .. math::

            measure_check(cthread, 1)

    2.  If method is not marked as terminating, we add a leak check:

        .. math::

            (perm(cthread) == none \land
                \text{leak check for other obligation types})

Loop Encoding
=============

1.  We save ``MustTerminate`` amount in a variable so that we can
    restore it after the loop (like in [C2SObligations]_). Otherwise,
    terminating loop in non-terminating method would generate
    termination obligations.
2.  We save loop's termination promise:
    :math:`termination_flag := tcond_no_measure`.
3.  Like in [C2SObligations]_, to distinguish if we are exhaling before
    the loop or after the loop, we use a boolean local variable
    ``exhale_before_loop_var``. Before loop it is set to ``True`` and at
    the end of the loop body – to ``False``.
4.  At the end of the loop invariant (similarly to [C2SObligations]_,
    but the check is not the same), we add a leak check that guarantees
    that either loop promised to terminate, or that context does not
    have any obligations:

    .. math::

        exhale_before_loop_var \Rightarrow
            \not{loop_condition} \lor
            termination_flag \lor
                (perm(cthread) == none \land
                    \text{leak check for other obligation types})

    .. note::

        This check is almost identical to the one for method encoding.

5.  At the end of the loop invariant (similarly to [C2SObligations]_),
    we add a leak check that guarantees that loop body does not leak
    obligations:

    .. math::

        !exhale_before_loop_var \Rightarrow (
            \text{leak check for other obligation types}
        )

    .. note::

        This leak check does not check if loop upholds its termination
        promise.

6.  At the end of loop body we add a check that loop upholds its promise
    to terminate:

    .. math::

        termination_flag \Rightarrow (tcond \lor \not{loop_condition})

.. rubric:: References

..  [C2SObligations]
    Verification of Finite Blocking in Chalice
    Robert Meier, SS 2015
    https://www.ethz.ch/content/dam/ethz/special-interest/infk/chair-program-method/pm/documents/Education/Theses/Robert%20_Meier_MA_report.pdf

..  [Obligations]
    Modular Verification of Finite Blocking in Non-terminating Programs
    P. Boström and P. Müller
    European Conference on Object-Oriented Programming (ECOOP), 2015.
    http://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=BostromMueller15.pdf
"""


import ast

from typing import Any, Dict, List, Optional

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Predicate,
)
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.translators.obligation.inexhale import (
    InexhaleObligationInstanceMixin,
    ObligationInhaleExhale,
)
from nagini_translation.translators.obligation.types.base import (
    ObligationInstance,
    Obligation,
)


_OBLIGATION_NAME = 'MustTerminate'
_PREDICATE_NAME = _OBLIGATION_NAME


def _create_predicate_access(cthread: PythonVar) -> sil.PredicateAccess:
    """Create a predicate access expression."""
    return sil.PredicateAccess(_PREDICATE_NAME, sil.RefVar(cthread))


class MustTerminateObligationInstance(
        InexhaleObligationInstanceMixin, ObligationInstance):
    """Class representing instance of ``MustTerminate`` obligation."""

    def __init__(
            self, obligation: 'MustTerminateObligation', node: ast.expr,
            measure: ast.expr, target: PythonVar) -> None:
        super().__init__(obligation, node)
        self._measure = measure
        self._target = target

    def _get_inexhale(self, ctx: Context) -> ObligationInhaleExhale:
        return ObligationInhaleExhale(
            _create_predicate_access(self._target),
            skip_exhale=True,
            skip_inhale=obligation_config.disable_termination_check)

    def get_obligation_bound(self, ctx: Context) -> sil.Statement:
        assert False    # MustTerminate is never fresh.

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
        elif (isinstance(node.func, ast.Name) and
              node.func.id == "TerminatesSif"):
              measure = node.args[1]
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

    def create_predicates(
            self, translator: CommonTranslator) -> List[Predicate]:
        if obligation_config.disable_termination_check:
            return []
        else:
            return super().create_predicates(translator)
