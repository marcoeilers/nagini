from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
    Requires,
    Ensures
)


@CallSlot
def some_call_slot(f: Callable[[Callable[[], None]], None], g: Callable[[], None]) -> None:
    f(g)


def some_global_hof_method(g: Callable[[], None]) -> None:
    pass


def some_global_method() -> None:
    pass


def method() -> None:

    f = some_global_hof_method
    g = some_global_method

    @CallSlotProof(some_call_slot(f, g))
    def call_slot_proof(f: Callable[[Callable[[], None]], None], g: Callable[[], None]) -> None:

        # justified because f == some_global_hof_method
        #:: ExpectedOutput(invalid.program:call_slot.names.non_local)
        ClosureCall(f(some_global_method), some_global_hof_method)  # type: int
