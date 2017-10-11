from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    CallSlotProof,
    ClosureCall,
)

some_global_var = 5  # type: int


def some_method(x: int) -> None:
    pass


@CallSlot
def some_call_slot(f: Callable[[int], None]) -> None:
    f(5)


def test_method() -> None:

    f = some_method

    @CallSlotProof(some_call_slot(f))
    def some_call_slot_proof(f: Callable[[int], None]) -> None:
        #:: ExpectedOutput(invalid.program:call_slot.names.non_local)
        ClosureCall(f(some_global_var), some_method)
