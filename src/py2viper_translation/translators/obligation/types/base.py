"""Base classes for obligations."""


import abc
import ast

from typing import Any, Dict, List, Optional

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.typedefs import (
    Predicate,
)
from py2viper_translation.translators.common import CommonTranslator


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
    def get_target(self) -> expr.RefExpression:
        """Return an expression to which obligation is attached."""

    @abc.abstractmethod
    def get_use_method(self, ctx: Context) -> expr.Expression:
        """Get inhale exhale pair for use in method contract."""

    @abc.abstractmethod
    def get_use_loop(self, ctx: Context) -> expr.Expression:
        """Get inhale exhale pair for use in loop invariant."""


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
            interface_dict: Dict[str, Any]) -> List[expr.BoolExpression]:
        """Add obligations to axiomatic method precondition."""

    @abc.abstractmethod
    def create_leak_check(self, var_name: str) -> List[expr.BoolExpression]:
        """Create a leak check for this obligation.

        :param var_name: variable name to be used in ``ForPerm``
        """

    def _create_predicate_for_perm(
            self, predicate_name: str, var_name: str) -> expr.ForPerm:
        """Create a ForPerm expression with predicate for use in leak check."""
        return expr.ForPerm(
            var_name,
            [expr.Predicate(predicate_name, var_name)],
            expr.FalseLit())

    def _create_field_for_perm(
            self, field_name: str, var_name: str) -> expr.ForPerm:
        """Create a ForPerm expression with field for use in leak check."""
        return expr.ForPerm(
            var_name,
            [expr.Field(field_name, expr.INT)],
            expr.FalseLit())

    def create_predicates(
            self, translator: CommonTranslator) -> List[Predicate]:
        """Create predicates that are used to represent this obligation."""
        position = translator.viper.NoPosition
        info = translator.viper.NoInfo
        predicates = [
            expr.Predicate(name, 'r')
            for name in self._predicate_names]
        translated_predicates = [
            predicate.translate(translator, None, position, info)
            for predicate in predicates]
        return translated_predicates

    def create_fields(
            self, translator: CommonTranslator) -> List[Predicate]:
        """Create fields that are used to represent this obligation."""
        position = translator.viper.NoPosition
        info = translator.viper.NoInfo
        fields = [
            expr.Field(name, expr.INT)
            for name in self._field_names]
        translated_fields = [
            field.translate(translator, None, position, info)
            for field in fields]
        return translated_fields
