from typing import Callable
from nagini_contracts.contracts import CallSlot


@CallSlot
#:: ExpectedOutput(invalid.program:call_slots.parameters.illegal_name)
def call_slot(Acc: Callable[[int], None]) -> None:
    Acc(2)
