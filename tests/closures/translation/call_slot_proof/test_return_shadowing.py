from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
    Requires,
    Ensures
)


def add(x: int, y: int) -> int:
    return x + y


def mul(x: int, y: int) -> int:
    return x * y


F_Type = Callable[[int, int], int]


@CallSlot
def call_slot(f: F_Type, x: int) -> None:

    @UniversallyQuantified
    def uq(y: int) -> None:
        Requires(x >= 0 and y > x)
        z = f(x, y)
        Ensures(z == y)


def method() -> None:

    x = 1
    f = add

    @CallSlotProof(call_slot(f, x))
    def call_slot_proof(f: F_Type, x: int) -> None:

        @UniversallyQuantified
        def uq(y: int) -> None:
            Requires(x >= 0 and y > x)

            # justified because f == add
            #:: ExpectedOutput(invalid.program:call_slots.parameters.illegal_shadowing)
            x = ClosureCall(f(x, y), add)  # type: int

            Ensures(x == y)
