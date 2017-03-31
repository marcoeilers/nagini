"""Functions and classes needed for writing obligation related contracts."""

# pragma pylint: disable=invalid-name,unused-argument


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


def Level(l: BaseLock) -> LevelType:
    """Level of the given lock."""


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
