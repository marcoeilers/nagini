from typing import Callable, Tuple
from nagini_contracts.contracts import (
    CallSlot,
    UniversallyQuantified,
    Requires,
    Ensures
)


@CallSlot
def call_slot(f: Callable[[int, int], Tuple[int, int, int, int]], x: int) -> None:

    @UniversallyQuantified
    def uq(y: int) -> None:
        Requires(x >= 0 and y > x)
        a, b, c, z = f(x, y)
        Ensures(z == x + y and b == c and a <= 0)
