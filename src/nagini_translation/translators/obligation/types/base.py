"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Base classes for obligations."""


import abc
import ast

from typing import Any, Dict, List, Optional, Tuple

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.context import Context
from nagini_translation.lib.errors import Rules
from nagini_translation.lib.program_nodes import (
    PythonMethod,
)
from nagini_translation.lib.typedefs import (
    Predicate,
    Field,
)
from nagini_translation.translators.common import CommonTranslator


class ObligationInstance(abc.ABC):
    """A base class for all obligation instances.

    Obligation instance is a concrete instantiation of a obligation with
    specific measure and other properties.
    """

    def __init__(self, obligation: 'Obligation', node: ast.expr) -> None:
        super().__init__()
        self.obligation = obligation
        """Actual obligation type."""
        self.node = node
        """AST node from which this obligation was instantiated."""

    @abc.abstractmethod
    def is_fresh(self) -> bool:
        """Return if this a fresh obligation."""

    @abc.abstractmethod
    def get_measure(self) -> "IntegerExpression":
        """Return an obligation measure.

        If obligation is fresh, the behaviour of this call is undefined.
        """

    @abc.abstractmethod
    def get_target(self) -> sil.RefExpression:
        """Return an expression to which obligation is attached."""

    @abc.abstractmethod
    def get_use_method(
            self, ctx: Context) -> List[Tuple[sil.Expression, Rules]]:
        """Get inhale exhale pair for use in method contract."""

    @abc.abstractmethod
    def get_use_loop(
            self, ctx: Context) -> List[Tuple[sil.Expression, Rules]]:
        """Get inhale exhale pair for use in loop invariant."""

    @abc.abstractmethod
    def get_obligation_bound(self, ctx: Context) -> sil.Statement:
        """Get exhale/inhale pair that bounds obligation."""


class Obligation(abc.ABC):
    """A base class for all obligations."""

    def __init__(self, predicate_names, field_names) -> None:
        self._predicate_names = predicate_names
        self._field_names = field_names

    @abc.abstractmethod
    def identifier(self) -> str:
        """Unique identifier of this obligation type."""

    @abc.abstractmethod
    def check_node(
            self, node: ast.Call,
            obligation_info: 'PythonMethodObligationInfo',
            method: PythonMethod) -> Optional[ObligationInstance]:
        """Check if node represents this obligation type.

        If check is successful, an obligation instance object is
        returned. Otherwise – ``None``.
        """

    @abc.abstractmethod
    def generate_axiomatized_preconditions(
            self, obligation_info: 'PythonMethodObligationInfo',
            interface_dict: Dict[str, Any]) -> List[sil.BoolExpression]:
        """Generate obligations for axiomatic method precondition."""

    @abc.abstractmethod
    def create_leak_check(self, var_name: str) -> List[sil.BoolExpression]:
        """Create a leak check for this obligation.

        :param var_name: variable name to be used in ``ForPerm``
        """

    def _create_predicate_for_perm(
            self, predicate_name: str, var_name: str) -> sil.ForPerm:
        """Create a ForPerm expression with predicate for use in leak check."""
        return sil.ForPerm(
            var_name,
            sil.Predicate(predicate_name, var_name),
            sil.FalseLit())

    def _create_field_for_perm(
            self, field_name: str, var_name: str) -> sil.ForPerm:
        """Create a ForPerm expression with field for use in leak check."""
        return sil.ForPerm(
            var_name,
            sil.Field(field_name, sil.INT),
            sil.FalseLit())

    def create_predicates(
            self, translator: CommonTranslator) -> List[Predicate]:
        """Create predicates that are used to represent this obligation."""
        position = translator.viper.NoPosition
        info = translator.viper.NoInfo
        predicates = [
            sil.Predicate(name, 'r')
            for name in self._predicate_names]
        translated_predicates = [
            predicate.translate(translator, None, position, info)
            for predicate in predicates]
        return translated_predicates

    def create_fields_untranslated(self) -> List[sil.Field]:
        """Create fields that are used to represent this obligation."""
        fields = [
            sil.Field(name, sil.INT)
            for name in self._field_names]
        return fields

    def create_fields(
            self, translator: CommonTranslator) -> List[Field]:
        """Create Silver fields that are used to represent this obligation."""
        position = translator.viper.NoPosition
        info = translator.viper.NoInfo
        translated_fields = [
            field.translate(translator, None, position, info)
            for field in self.create_fields_untranslated()]
        return translated_fields
