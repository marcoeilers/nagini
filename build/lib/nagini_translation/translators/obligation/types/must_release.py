"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""``MustRelease`` obligation implementation."""


import ast

from typing import Any, Dict, List, Optional

from nagini_translation.lib import silver_nodes as sil
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


_OBLIGATION_NAME = 'MustRelease'
_BOUNDED_FIELD_NAME = _OBLIGATION_NAME + 'Bounded'
_UNBOUNDED_FIELD_NAME = _OBLIGATION_NAME + 'Unbounded'


class MustReleaseObligationInstance(
        InexhaleObligationInstanceMixin, ObligationInstance):
    """Class representing instance of ``MustRelease`` obligation."""

    def __init__(
            self, obligation: 'MustReleaseObligation', node: ast.expr,
            measure: Optional[ast.expr], target: ast.expr) -> None:
        super().__init__(obligation, node)
        self._measure = measure
        self._target = target

    def _get_inexhale(self, ctx: Context) -> ObligationInhaleExhale:
        return ObligationInhaleExhale(
            sil.FieldAccess(
                self.get_target(), _BOUNDED_FIELD_NAME, sil.INT),
            sil.FieldAccess(
                self.get_target(), _UNBOUNDED_FIELD_NAME, sil.INT))

    def is_fresh(self) -> bool:
        return self._measure is None

    def get_measure(self) -> sil.IntExpression:
        assert not self.is_fresh()
        return sil.PythonIntExpression(self._measure)

    def get_target(self) -> sil.RefExpression:
        return sil.PythonRefExpression(self._target)


class MustReleaseObligation(Obligation):
    """Class representing ``MustRelease`` obligation."""

    def __init__(self) -> None:
        super().__init__([], [
            _BOUNDED_FIELD_NAME,
            _UNBOUNDED_FIELD_NAME])

    def identifier(self) -> str:
        return _OBLIGATION_NAME

    def check_node(
            self, node: ast.Call,
            obligation_info: 'PythonMethodObligationInfo',
            method: PythonMethod) -> Optional[MustReleaseObligationInstance]:
        if (isinstance(node.func, ast.Name) and
                node.func.id == _OBLIGATION_NAME):
            target = node.args[0]
            measure = node.args[1] if len(node.args) > 1 else None
            instance = MustReleaseObligationInstance(
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
            self._create_field_for_perm(_BOUNDED_FIELD_NAME, var_name),
            self._create_field_for_perm(_UNBOUNDED_FIELD_NAME, var_name),
        ]
