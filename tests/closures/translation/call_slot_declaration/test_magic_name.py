from typing import Callable
from nagini_contracts.contracts import CallSlot


#:: ExpectedOutput(invalid.program:illegal.magic.method)
@CallSlot
def __call_slot__(f: Callable[[int], None]) -> None:
    f(2)
