from typing import Callable
from nagini_contracts.contracts import CallSlot


def some_gloval_method() -> None:
    pass


@CallSlot
def some_call_slot(f: Callable[[Callable[[], None]], None]) -> None:
    #:: ExpectedOutput(invalid.program:call_slot.names.non_local)
    f(some_gloval_method)
