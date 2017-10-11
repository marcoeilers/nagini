from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    UniversallyQuantified,
    Requires,
    Ensures,
    Old
)


@CallSlot
def call_slot(f: Callable[[int, int], int], x: int) -> None:

    @UniversallyQuantified
    def uq(y: int) -> None:
        Requires(x >= 0 and y > x)
        #:: ExpectedOutput(invalid.program:call_slots.parameters.illegal_shadowing)
        y = f(x, y)
        Ensures(y == x + Old(y))
