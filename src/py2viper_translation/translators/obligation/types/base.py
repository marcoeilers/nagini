"""Base classes for obligations."""


import abc
import ast

from typing import List, Optional

from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Predicate,
)
from py2viper_translation.translators.common import CommonTranslator
from py2viper_translation.translators.obligation.utils import (
    create_obligation_predicate,
)


class ObligationInstance(abc.ABC):
    """A base class for all obligation instances.

    Obligation instance is a concrete instantiation of a obligation with
    specific measure and other properties.
    """

    def __init__(self, node: ast.expr) -> None:
        super().__init__()
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
    def get_target(self) -> PythonVar:
        """Return a variable to which obligation is attached."""


class Obligation(abc.ABC):
    """A base class for all obligations."""

    def __init__(self, predicate_names) -> None:
        self._predicate_names = predicate_names

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

    def create_predicates(
            self, translator: CommonTranslator) -> List[Predicate]:
        """Create predicates that are used to represent this obligation."""
        predicates = [
            create_obligation_predicate(name, translator)
            for name in self._predicate_names]
        return predicates
