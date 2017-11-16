from typing import Callable
from nagini_contracts.contracts import CallSlot


def method_with_call_slot_inside() -> None:

    #:: ExpectedOutput(invalid.program:call_slots.nested.declaration)
    @CallSlot
    def call_slot(f: Callable[[int], None]) -> None:
        f(2)
