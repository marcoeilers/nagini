from typing import Callable, Optional
from nagini_contracts.contracts import (
    Requires,
    Ensures,
    Predicate,
    Acc,
    Old,
    CallSlot,
    CallSlotProof,
    ClosureCall,
)


class Argument:

    def __init__(self, parameter: int, result: int) -> None:
        self.parameter = parameter  # type: int
        self.result = result  # type: int

        Ensures(Acc(self.parameter) and Acc(self.result))
        Ensures(self.parameter == parameter and self.result == result)


inc_type = Callable[[Argument], Optional[object]]


def inc(argm: Argument) -> Optional[object]:
    Requires(Acc(argm.parameter) and Acc(argm.result))

    Ensures(Acc(argm.parameter) and Acc(argm.result))
    Ensures(argm.result == Old(argm.result) + argm.parameter)
    Ensures(argm.parameter == Old(argm.parameter))

    argm.result = argm.result + argm.parameter

    return None


@CallSlot
def inc_call_slot(f: inc_type, argm: Argument) -> None:
    Requires(Acc(argm.parameter) and Acc(argm.result))

    f(argm)

    Ensures(Acc(argm.parameter) and Acc(argm.result))
    Ensures(argm.result >= Old(argm.result) + argm.parameter)
    Ensures(argm.parameter == Old(argm.parameter))


def test() -> None:

    argm = Argument(1, 2)

    argm.result = 20
    argm.parameter = 50

    f = inc

    @CallSlotProof(inc_call_slot(inc, argm))
    def inc_proof(f: inc_type, argm: Argument) -> None:
        Requires(Acc(argm.parameter) and Acc(argm.result))

        ClosureCall(f(argm), inc)

        Ensures(Acc(argm.parameter) and Acc(argm.result))
        Ensures(argm.result >= Old(argm.result) + argm.parameter)
        Ensures(argm.parameter == Old(argm.parameter))

    ClosureCall(f(argm), inc_call_slot(f, argm)())

    assert argm.result >= 70 and argm.parameter == 50
