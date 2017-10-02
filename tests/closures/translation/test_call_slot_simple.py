from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    UniversallyQuantified,
    Requires,
    Ensures
)


@CallSlot
def call_slot(f: Callable[[int, int], int], x: int) -> None:

    @UniversallyQuantified
    def uq(y: int) -> None:
        Requires(x >= 0 and y > x)
        z = f(x, y)
        Ensures(z == x + y)
