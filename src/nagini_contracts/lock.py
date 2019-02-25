"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""The lock class stub."""

from typing import Generic, Optional, TypeVar

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Implies,
    Low,
    LowEvent,
    Predicate,
    Pure,
    Requires,
)
from nagini_contracts.obligations import (
    BaseLock,
    Level,
    MustRelease,
    MustTerminate,
    WaitLevel,
)


T = TypeVar("T")


class Lock(BaseLock, Generic[T]):
    """A stub for a lock that protects (parts of) the state of an object of type T."""

    def __init__(self, locked_object: T,
                 above: Optional[BaseLock]=None,
                 below: Optional[BaseLock]=None) -> None:
        """
        Create a lock whose level is below that of ``below`` and above that of ``above``,
        which protects ``locked_object``.
        Creating the lock "shares" the object (i.e., exhales the invariant).
        Create subclasses of this class and override ``invariant`` to create a lock
        with an invariant.

        ``Level(above)`` defaults to ``WaitLevel()``.
        """
        Requires(MustTerminate(1))
        Requires(Implies(above is None and below is not None,
                         WaitLevel() < Level(below)))
        Requires(Implies(above is not None and below is not None,
                         Level(above) < Level(below)))
        Requires(self.invariant())
        Ensures(Implies(above is None, WaitLevel() < Level(self)))
        Ensures(Implies(above is not None, Level(above) < Level(self)))
        Ensures(Implies(below is not None, Level(self) < Level(below)))

    @Pure
    @ContractOnly
    def get_locked(self) -> T:
        """Returns the object protected by this lock."""

    @Predicate
    def invariant(self) -> bool:
        """
        The lock invariant, expressed in terms of ``self.get_locked()``. Override this
        in a subclass to create a lock with an invariant.
        """
        return True

    @ContractOnly
    def acquire(self) -> None:
        """Acquire the lock."""
        Requires(MustTerminate(1))
        Requires(WaitLevel() < Level(self))
        Requires(Low(self))
        Requires(LowEvent())
        Ensures(self.invariant())
        Ensures(MustRelease(self))

    @ContractOnly
    def release(self) -> None:
        """Release the lock."""
        Requires(MustTerminate(1))
        Requires(MustRelease(self, 1))
        Requires(self.invariant())
        Requires(Low(self))
        Requires(LowEvent())
