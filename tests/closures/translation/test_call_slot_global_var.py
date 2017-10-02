from typing import Callable
from nagini_contracts.contracts import CallSlot

some_gloval_var = 5  # type: int

@CallSlot
def some_call_slot(f: Callable[[int], None]) -> None:
    #:: ExpectedOutput(invalid.program:call_slot.names.non_local)
    f(some_gloval_var)
