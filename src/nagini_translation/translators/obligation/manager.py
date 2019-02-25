"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Singleton for managing obligations."""


from typing import List

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.typedefs import (
    Predicate,
)
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.translators.obligation.types.base import (
    Obligation,
)
from nagini_translation.translators.obligation.types.must_terminate import (
    MustTerminateObligation,
)
from nagini_translation.translators.obligation.types.must_invoke import (
    MustInvokeObligation,
)
from nagini_translation.translators.obligation.types.must_release import (
    MustReleaseObligation,
)


class ObligationManager:
    """Class that knows about all obligation types."""

    def __init__(self) -> None:
        self._must_terminate_obligation = MustTerminateObligation()
        self._must_invoke_obligation = MustInvokeObligation()
        self._must_release_obligation = MustReleaseObligation()
        self._obligations = [
            self._must_terminate_obligation,
            self._must_invoke_obligation,
            self._must_release_obligation,
        ]

    @property
    def must_terminate_obligation(self) -> MustTerminateObligation:
        """Get ``MustTerminate`` obligation."""
        return self._must_terminate_obligation

    @property
    def must_invoke_obligation(self) -> MustInvokeObligation:
        """Get ``MustInvoke`` obligation."""
        return self._must_invoke_obligation

    @property
    def must_release_obligation(self) -> MustReleaseObligation:
        """Get ``MustRelease`` obligation."""
        return self._must_release_obligation

    @property
    def obligations(self) -> List[Obligation]:
        """Get a list of all obligations."""
        return self._obligations

    def create_predicates(
            self, translator: CommonTranslator) -> List[Predicate]:
        """Get all predicates that are used to represent obligations."""
        predicates = []
        for obligation in self._obligations:
            predicates.extend(obligation.create_predicates(translator))
        return predicates

    def create_fields(
            self, translator: CommonTranslator) -> List[Predicate]:
        """Get all fields that are used to represent obligations."""
        fields = []
        for obligation in self._obligations:
            fields.extend(obligation.create_fields(translator))
        return fields

    def create_leak_check(
            self, var_name: str) -> sil.BoolExpression:
        """Create a leak check for all obligation except termination."""
        checks = []
        for obligation in self._obligations:
            if obligation is self._must_terminate_obligation:
                continue
            checks.extend(obligation.create_leak_check(var_name))
        return sil.BigAnd(checks)
