from typing import Callable, Tuple
from nagini_contracts.contracts import (
    Requires,
    Ensures,
    Invariant,
    Acc,
    Result,
    Pure,
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
)

#:: IgnoreFile(42)
# Call slot support isn't implemented enough at the moment.

@Pure
def idiv(x: int, y: int) -> int:
    Requires(y != 0)


@Pure
def sqrt(x: int) -> int:
    Requires(x >= 0)


@Pure
def log(x: int) -> int:
    Requires(x > 0)


def choice() -> bool:
    pass


class Argument:

    def __init__(self, parameter: int, result: int) -> None:
        self.parameter = parameter  # type: int
        self.result = result  # type: int

        Ensures(Acc(self.parameter) and Acc(self.result))
        Ensures(self.parameter == parameter and self.result == result)


G_Type = Callable[[Argument, int, int], Tuple[int, int]]


@CallSlot
def func_call_slot(g: G_Type, b: int, c: int) -> None:

    @UniversallyQuantified
    def uq(a: Argument) -> None:

        Requires(Acc(a.parameter, 1 / 2) and Acc(a.result))
        Requires(a.parameter >= b + c)

        ret = g(a, b, c)

        Ensures(Acc(a.parameter, 1 / 2) and Acc(a.result))
        Ensures(a.result != 0 and ret[0] >= 0 and ret[1] > 0)


def func(
        g: G_Type,
        a: Argument,
        b: int,
        c: int
) -> Tuple[int, int, int]:

    Requires(func_call_slot(g, b, c))
    Requires(Acc(a.parameter))
    Requires(Acc(a.result))
    Ensures(Acc(a.parameter))
    Ensures(Acc(a.result))

    while a.parameter < b + c:
        Invariant(Acc(a.parameter))
        a.parameter = a.parameter * a.parameter

    # g reads a.parameter and writes to a.result

    # closure call justified because the call slot holds:
    # func_call_slot(g, b, c)
    d, e = ClosureCall(g(a, b, c), func_call_slot(g, b, c)(a))  # type: Tuple[int, int]

    return idiv(1, a.result), sqrt(d), log(e)


def concrete_g_1(a: Argument, b: int, c: int) -> Tuple[int, int]:
    Requires(Acc(a.parameter, 1 / 2) and Acc(a.result))
    Requires(a.parameter >= b + c)
    Ensures(Acc(a.parameter, 1 / 2) and Acc(a.result))
    Ensures(a.result == -1 and Result()[0] == 0 and Result()[1] >= 1)

    a.result = -1
    return 0, a.parameter - b - c + 1


def concrete_g_2(a: Argument, b: int, c: int) -> Tuple[int, int]:
    Requires(Acc(a.parameter, 1 / 2) and Acc(a.result))
    Requires(a.parameter >= b + c)
    Ensures(Acc(a.parameter, 1 / 2) and Acc(a.result))
    Ensures(a.result == 1 and Result()[0] >= 0 and Result()[1] == 1)

    a.result = 1
    return a.parameter - b - c, 1


def client() -> None:

    if choice():  # non-deterministic choice
        concrete_g = concrete_g_1
    else:
        concrete_g = concrete_g_2

    a = Argument(2, 2)
    b, c = 2, 3

    @CallSlotProof(func_call_slot(concrete_g, b, c))
    def func_call_slot_proof(concrete_g: G_Type, b: int, c: int) -> None:

        @UniversallyQuantified
        def uq(a: Argument, d: int, e: int) -> None:

            Requires(Acc(a.parameter, 1 / 2) and Acc(a.result))
            Requires(a.parameter >= b + c)

            if concrete_g == concrete_g_1:
                # closure call justified, because we can prove static dispatch:
                # concrete_g == concrete_g_1
                # and concrete_g_1 is a method whose contracts we can look up
                # statically/in nagini
                ret = ClosureCall(concrete_g(a, b, c), concrete_g_1)  # type: Tuple[int, int]
            else:
                assert concrete_g == concrete_g_2
                # closure call justified, because we can prove static dispatch:
                # concrete_g == concrete_g_2
                # and concrete_g_2 is a method whose contracts we can look up
                # statically/in nagini
                ret = ClosureCall(concrete_g(a, b, c), concrete_g_2)

            Ensures(Acc(a.parameter, 1 / 2) and Acc(a.result))
            Ensures(a.result != 0 and ret[0] >= 0 and ret[1] > 0)

    func(concrete_g, a, b, c)
