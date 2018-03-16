from typing import Callable
from nagini_contracts.contracts import (
    Requires,
    Ensures,
    Acc,
    Pure,
    Result,
    Old,
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall
)


def choice() -> bool:
    return True


class Argument:

    def __init__(self, parameter: int, result: int) -> None:
        self.parameter = parameter  # type: int
        self.result = result  # type: int

        Ensures(Acc(self.parameter) and Acc(self.result))
        Ensures(self.parameter == parameter and self.result == result)


F_Type = Callable[[Argument, int], int]


@Pure
def add(argm: Argument, x: int) -> int:
    Requires(Acc(argm.parameter))
    Ensures(Result() == x + argm.parameter)
    return x + argm.parameter


@Pure
def mul(argm: Argument, x: int) -> int:
    Requires(Acc(argm.parameter))
    Ensures(Result() == x * argm.parameter)
    return x * argm.parameter


@Pure
@CallSlot
def pure_call_slot(f: F_Type, argm: Argument) -> None:

    @UniversallyQuantified
    def uq(x: int) -> None:
        Requires(Acc(argm.parameter) and argm.parameter > 0 and x > 1)

        y = f(argm, x)

        Ensures(y > argm.parameter)


def client(f: F_Type, argm: Argument) -> None:
    Requires(Acc(argm.parameter) and Acc(argm.result))
    Requires(argm.parameter > 0)
    Requires(pure_call_slot(f, argm))
    Ensures(Acc(argm.parameter) and Acc(argm.result))
    Ensures(argm.parameter == Old(argm.parameter))
    Ensures(argm.result > argm.parameter)

    argm.result = ClosureCall(f(argm, 20), pure_call_slot(f, argm)(20))


def method() -> None:

    if choice():
        f = add
    else:
        f = mul

    argm = Argument(10, 5)

    @CallSlotProof(pure_call_slot(f, argm))
    def pure_call_slot(f: F_Type, argm: Argument) -> None:

        @UniversallyQuantified
        def uq(x: int) -> None:
            Requires(Acc(argm.parameter) and argm.parameter > 0 and x > 1)

            if f == add:
                y = ClosureCall(f(argm, x), add)  # type: int
            else:
                y = ClosureCall(f(argm, x), mul)

            Ensures(y > argm.parameter)

    client(f, argm)

    assert argm.parameter == 10
    assert argm.result > argm.parameter
