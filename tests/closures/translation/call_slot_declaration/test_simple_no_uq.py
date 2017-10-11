from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    Requires,
    Ensures
)


@CallSlot
def call_slot(f: Callable[[int], int], x: int) -> None:
    Requires(x >= 0)
    z = f(x)
    Ensures(z >= x)
