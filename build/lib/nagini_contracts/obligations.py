"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Functions and classes needed for writing obligation related contracts."""

# pragma pylint: disable=invalid-name,unused-argument


from typing import Union
from nagini_contracts.thread import Thread


OBLIGATION_CONTRACT_FUNCS = [
    'MustTerminate',
    'MustRelease',
    'Level',
    'WaitLevel',
]


class BaseLock:
    """A base class for locks."""


class LevelType:
    """A type returned by ``Level`` function."""

    def __lt__(self, other: 'LevelType') -> bool:
        """We allow to compare only ``LevelType`` objects."""


def WaitLevel() -> LevelType:
    """The wait level of the current thread."""


def Level(l: Union[BaseLock, Thread]) -> LevelType:
    """Level of the given lock or thread."""


def MustRelease(lock: BaseLock, measure: int = None) -> bool:
    """An obligation to release a ``lock`` in ``measure`` steps."""


def MustTerminate(measure: int) -> bool:
    """An obligation to terminate in ``measure`` steps."""


__all__ = (
    'MustRelease',
    'MustTerminate',
    'LevelType',
    'WaitLevel',
    'Level',
)
