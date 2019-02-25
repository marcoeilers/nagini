"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""``MustInvoke`` obligation implementation."""


import ast

from typing import Any, Dict, List, Optional

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
)
from nagini_translation.translators.obligation.inexhale import (
    InexhaleObligationInstanceMixin,
    ObligationInhaleExhale,
)
from nagini_translation.translators.obligation.types.base import (
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

    def _get_inexhale(self, ctx: Context) -> ObligationInhaleExhale:
        return ObligationInhaleExhale(
            sil.PredicateAccess(_BOUNDED_PREDICATE_NAME, self.get_target()),
            sil.PredicateAccess(_UNBOUNDED_PREDICATE_NAME, self.get_target()),
            sil.PredicateAccess(_CREDIT_PREDICATE_NAME, self.get_target()),
            credit_only=obligation_config.disable_must_invoke)

    def is_fresh(self) -> bool:
        return self._measure is None

    def get_measure(self) -> sil.IntExpression:
        assert not self.is_fresh()
        return sil.PythonIntExpression(self._measure)

    def get_target(self) -> sil.RefExpression:
        return sil.PythonRefExpression(self._target)


class MustInvokeObligation(Obligation):
    """Class representing ``MustInvoke`` obligation."""

    def __init__(self) -> None:
        if obligation_config.disable_must_invoke:
            super().__init__([_CREDIT_PREDICATE_NAME], [])
        else:
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
            interface_dict: Dict[str, Any]) -> List[sil.BoolExpression]:
        return []

    def create_leak_check(self, var_name: str) -> List[sil.BoolExpression]:
        return [
            self._create_predicate_for_perm(
                _BOUNDED_PREDICATE_NAME, var_name),
            self._create_predicate_for_perm(
                _UNBOUNDED_PREDICATE_NAME, var_name),
        ]

    def create_ctoken_use(self, node: ast.Call) -> sil.Acc:
        """Create a ``ctoken`` use in contract."""
        target = sil.PythonRefExpression(node.args[0])
        return sil.Acc(sil.PredicateAccess(_CREDIT_PREDICATE_NAME, target))
