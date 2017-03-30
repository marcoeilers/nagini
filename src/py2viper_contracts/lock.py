"""The lock class stub."""

from typing import Optional

from py2viper_contracts.contracts import (
    Ensures,
    Implies,
    Requires,
)
from py2viper_contracts.obligations import (
    BaseLock,
    Level,
    MustRelease,
    MustTerminate,
    WaitLevel,
)


class Lock(BaseLock):
    """A stub for locks."""

    def __init__(self,
                 above: Optional['Lock']=None,
                 below: Optional['Lock']=None) -> None:
        """Create a lock at the specified level.

        ``Level(above)`` defaults to ``WaitLevel()``.
        """
        Requires(MustTerminate(1))
        Requires(Implies(above is None and below is not None,
                         WaitLevel() < Level(below)))
        Requires(Implies(above is not None and below is not None,
                         Level(above) < Level(below)))
        Ensures(Implies(above is None, WaitLevel() < Level(self)))
        Ensures(Implies(above is not None, Level(above) < Level(self)))
        Ensures(Implies(below is not None, Level(self) < Level(below)))

    def acquire(self) -> None:
        """Acquire the lock."""
        Requires(MustTerminate(1))
        Requires(WaitLevel() < Level(self))
        Ensures(MustRelease(self))

    def release(self) -> None:
        """Release the lock."""
        Requires(MustTerminate(1))
        Requires(MustRelease(self, 1))
