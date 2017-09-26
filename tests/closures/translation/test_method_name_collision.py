from typing import Callable
from nagini_contracts.contracts import *


def some_name() -> None:
    pass

#:: ExpectedOutput(type.error:Name 'some_name' already defined)
@CallSlot
def some_name(f: Callable[[int], None]) -> None:
    f(2)
