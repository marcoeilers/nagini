from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    CallSlotProof,
    ClosureCall,
    Requires,
    Ensures
)


def inc(x: int) -> int:
    return x + 1


def twice(x: int) -> int:
    return 2 * x


F_Type = Callable[[int], int]


@CallSlot
def call_slot(f: F_Type, x: int) -> None:

    Requires(x >= 0)
    z = f(x)
    Ensures(z >= x)


def method() -> None:

    x = 1
    f = inc

    @CallSlotProof(call_slot(f, x))
    def call_slot_proof(f: F_Type, x: int) -> None:

        Requires(x >= 0)

        # justified because f == add
        z = ClosureCall(f(x), inc)  # type: int

        Ensures(z >= x)
