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


def inc(arg: Argument) -> Optional[object]:
    Requires(Acc(arg.parameter) and Acc(arg.result))

    Ensures(Acc(arg.parameter) and Acc(arg.result))
    Ensures(arg.result == Old(arg.result) + arg.parameter)
    Ensures(arg.parameter == Old(arg.parameter))

    arg.result = arg.result + arg.parameter

    return None


@CallSlot
def inc_call_slot(f: inc_type, arg: Argument) -> None:
    Requires(Acc(arg.parameter) and Acc(arg.result))

    f(arg)

    Ensures(Acc(arg.parameter) and Acc(arg.result))
    Ensures(arg.result >= Old(arg.result) + arg.parameter)
    Ensures(arg.parameter == Old(arg.parameter))


def test() -> None:

    arg = Argument(1, 2)

    arg.result = 20
    arg.parameter = 50

    f = inc

    @CallSlotProof(inc_call_slot(inc, arg))
    def inc_proof(f: inc_type, arg: Argument) -> None:
        Requires(Acc(arg.parameter) and Acc(arg.result))

        ClosureCall(f(arg), inc)

        Ensures(Acc(arg.parameter) and Acc(arg.result))
        Ensures(arg.result >= Old(arg.result) + arg.parameter)
        Ensures(arg.parameter == Old(arg.parameter))

    ClosureCall(f(arg), inc_call_slot(f, arg)())

    assert arg.result >= 70 and arg.parameter == 50
