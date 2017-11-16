from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    UniversallyQuantified,
    Requires,
    Ensures,
    Acc,
    Fold
)


@CallSlot
def call_slot(f: Callable[[int, int], int], arg: 'Arg') -> None:

    @UniversallyQuantified
    def uq(y: int) -> None:
        #:: ExpectedOutput(invalid.program:purity.violated)
        Requires(is_arg(arg) and y > 0)
        z = f(arg.val, y)
        Ensures(z >= y)


class Arg:

    def __init__(self) -> None:
        Ensures(Acc(self.val))
        self.val = 1  # type: int


def is_arg(arg: Arg) -> bool:
    return True
