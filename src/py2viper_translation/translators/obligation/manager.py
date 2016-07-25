"""Singleton for managing obligations."""


from typing import List

from py2viper_translation.lib.typedefs import (
    Predicate,
)
from py2viper_translation.translators.common import CommonTranslator
from py2viper_translation.translators.obligation.types.must_terminate import (
    MustTerminateObligation,
)


class ObligationManager:
    """Class that knows about all obligation types."""

    def __init__(self) -> None:
        self._must_terminate_obligation = MustTerminateObligation()
        self._obligations = [
            self._must_terminate_obligation,
        ]

    @property
    def must_terminate_obligation(self) -> MustTerminateObligation:
        """Get ``MustTerminate`` obligation."""
        return self._must_terminate_obligation

    def create_predicates(
            self, translator: CommonTranslator) -> List[Predicate]:
        """Get all predicates that are used to represent obligations."""
        predicates = []
        for obligation in self._obligations:
            predicates.extend(obligation.create_predicates(translator))
        return predicates


obligation_manager = ObligationManager()    # pylint: disable=invalid-name
