from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    CallSlotProof,
    ClosureCall,
    Requires,
    Ensures
)


def add(x: int, y: int) -> int:
    return x + y


def mul(x: int, y: int) -> int:
    return x * y


F_Type = Callable[[int], int]


@CallSlot
def call_slot(f: F_Type, x: int) -> None:

    Requires(x >= 0)
    z = f(x)
    Ensures(z >= x)


def method() -> None:

    x = 1
    f = add

    @CallSlotProof(call_slot(f, x))
    #:: ExpectedOutput(invalid.program:call_slots.parameters.illegal_name)
    def call_slot_proof(Acc: F_Type, x: int) -> None:
        Requires(x >= 0)

        # justified because f == add
        z = ClosureCall(Acc(x), add)  # type: int
        Ensures(z >= x)
