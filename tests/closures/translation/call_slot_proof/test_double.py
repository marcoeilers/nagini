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


F_Type = Callable[[int, int], None]


@CallSlot
def call_slot(f: F_Type, x: int) -> None:

    @UniversallyQuantified
    def uq(y: int) -> None:
        Requires(x >= 0 and y > x)
        f(x, y)


def method() -> None:

    x = 1
    f = add

    #:: IgnoreFile(42)
    # Implementation not far enough yet
    @CallSlotProof(call_slot(f, x))
    def call_slot_proof1(f: F_Type, x: int) -> None:

        @UniversallyQuantified
        def uq(y: int) -> None:
            Requires(x >= 0 and y > x)

            # justified because f == add
            ClosureCall(f(x, y), add)  # type: int

    @CallSlotProof(call_slot(f, x))
    def call_slot_proof2(f: F_Type, x: int) -> None:

        @UniversallyQuantified
        def uq(y: int) -> None:
            Requires(x >= 0 and y > x)

            # justified because f == add
            ClosureCall(f(x, y), add)  # type: int
