from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
    Requires,
    Ensures,
    Acc
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
        Ensures(z == x + y)


class A:

    def __init__(self) -> None:
        self.call_slot = call_slot  # type: Callable
        Ensures(Acc(self.call_slot))


def method(f: F_Type, x: int) -> None:
    Requires(call_slot(f, x))

    y = 1
    a = A()

    #:: ExpectedOutput(invalid.program:call_slots.closure_call.invalid_justification)
    z = ClosureCall(f(x, y), (a.call_slot)(f, x)(y))  # type: int
