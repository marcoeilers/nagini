from typing import Callable
from nagini_contracts.contracts import CallSlot


class class_with_call_slot_inside:

    #:: ExpectedOutput(invalid.program:call_slots.nested.declaration)
    @CallSlot
    def call_slot(self, f: Callable[[int], None]) -> None:
        f(2)
