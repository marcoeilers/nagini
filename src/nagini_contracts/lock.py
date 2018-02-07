"""
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


T = TypeVar('T')


class Lock(BaseLock, Generic[T]):
    """A stub for locks."""

    def __init__(self, locked_object: T,
                 above: Optional[BaseLock]=None,
                 below: Optional[BaseLock]=None) -> None:
        """Create a lock at the specified level.

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
        pass

    @Predicate
    def invariant(self) -> bool:
        return True

    @ContractOnly
    def acquire(self) -> None:
        """Acquire the lock."""
        Requires(MustTerminate(1))
        Requires(WaitLevel() < Level(self))
        Ensures(self.invariant())
        Ensures(MustRelease(self))

    @ContractOnly
    def release(self) -> None:
        """Release the lock."""
        Requires(MustTerminate(1))
        Requires(MustRelease(self, 1))
        Requires(self.invariant())
