from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    UniversallyQuantified,
    Requires,
    Ensures,
    Acc,
    Predicate,
    Fold
)


@CallSlot
def call_slot(f: Callable[[int, int], int], arg: 'Arg') -> None:

    @UniversallyQuantified
    def uq(y: int) -> None:
        Requires(is_arg(arg) and y > 0)
        z = f(arg.val, y)
        Ensures(z >= y)


class Arg:

    def __init__(self) -> None:
        Ensures(is_arg(self))
        self.val = 1  # type: int
        Fold(is_arg(self))


@Predicate
def is_arg(arg: Arg) -> bool:
    return Acc(arg.val)
