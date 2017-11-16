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
def add(arg: Argument, x: int) -> int:
    Requires(Acc(arg.parameter))
    Ensures(Result() == x + arg.parameter)
    return x + arg.parameter


@Pure
def mul(arg: Argument, x: int) -> int:
    Requires(Acc(arg.parameter))
    Ensures(Result() == x * arg.parameter)
    return x * arg.parameter


@Pure
@CallSlot
def pure_call_slot(f: F_Type, arg: Argument) -> None:

    @UniversallyQuantified
    def uq(x: int) -> None:
        Requires(Acc(arg.parameter) and arg.parameter > 0 and x > 1)

        y = f(arg, x)

        Ensures(y > arg.parameter)


def client(f: F_Type, arg: Argument) -> None:
    Requires(Acc(arg.parameter) and Acc(arg.result))
    Requires(arg.parameter > 0)
    Requires(pure_call_slot(f, arg))
    Ensures(Acc(arg.parameter) and Acc(arg.result))
    Ensures(arg.parameter == Old(arg.parameter))
    Ensures(arg.result > arg.parameter)

    arg.result = ClosureCall(f(arg, 20), pure_call_slot(f, arg)(20))


def method() -> None:

    if choice():
        f = add
    else:
        f = mul

    arg = Argument(10, 5)

    @CallSlotProof(pure_call_slot(f, arg))
    def pure_call_slot(f: F_Type, arg: Argument) -> None:

        @UniversallyQuantified
        def uq(x: int) -> None:
            Requires(Acc(arg.parameter) and arg.parameter > 0 and x > 1)

            if f == add:
                y = ClosureCall(f(arg, x), add)  # type: int
            else:
                y = ClosureCall(f(arg, x), mul)

            Ensures(y > arg.parameter)

    client(f, arg)

    assert arg.parameter == 10
    assert arg.result > arg.parameter
