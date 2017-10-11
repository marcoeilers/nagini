from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    UniversallyQuantified
)


@CallSlot
def some_slot(f: Callable[[int], None], x: int) -> None:

    @UniversallyQuantified
    #:: ExpectedOutput(invalid.program:call_slots.parameters.illegal_shadowing)
    def uq(x: int) -> None:
        f(x)

