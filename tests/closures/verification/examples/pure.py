from typing import Callable
from nagini_contracts.contracts import (
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
    Pure,
    Result,
    Requires,
    Ensures,
    Acc
)


def choice() -> bool:
    return True


class Argument:

    def __init__(self, value_a: int, value_b: int) -> None:
        self.value_a = value_a
        self.value_b = value_b
        Ensures(Acc(self.value_a) and Acc(self.value_b))
        Ensures(self.value_a == value_a and self.value_b == value_b)


f_type = Callable[[Argument, int], int]


@Pure
def add(argm: Argument, x: int) -> int:
    Requires(Acc(argm.value_a))
    Ensures(Result() == argm.value_a + x)
    return argm.value_a + x


@Pure
def mul(argm: Argument, x: int) -> int:
    Requires(Acc(argm.value_b))
    Ensures(Result() == argm.value_b * x)
    return argm.value_b * x


@Pure
@CallSlot
def add_or_mul(f: f_type) -> None:

    @UniversallyQuantified
    def uq(argm: Argument, x: int) -> None:
        Requires(Acc(argm.value_a) and Acc(argm.value_b))

        y = f(argm, x)

        Ensures(y == argm.value_a + x or y == argm.value_b * x)


@CallSlot
def hof_slot(f: f_type) -> None:

    @UniversallyQuantified
    def uq(argm: Argument, x: int) -> None:
        Requires(Acc(argm.value_a, 1 / 2) and Acc(argm.value_b, 1 / 3))

        y = f(argm, x)

        Ensures(Acc(argm.value_a, 1 / 2) and Acc(argm.value_b, 1 / 3))
        Ensures(y <= argm.value_a + x or y >= argm.value_b * x)


def hof(f: f_type, argm: Argument) -> int:
    Requires(Acc(argm.value_a, 1 / 2) and Acc(argm.value_b, 1 / 3))
    Requires(hof_slot(f))

    Ensures(Acc(argm.value_a, 1 / 2) and Acc(argm.value_b, 1 / 3))
    Ensures(Result() <= argm.value_a + 5 or Result() >= argm.value_b * 5)

    return ClosureCall(f(argm, 5), hof_slot(f)(argm, 5))


def client() -> None:

    argm = Argument(1, 2)
    assert argm.value_a == 1
    assert argm.value_b == 2

    f = add
    y = ClosureCall(f(argm, 3), add)  # type: int
    assert y == 4
    assert argm.value_a == 1
    assert argm.value_b == 2

    f = mul
    y = ClosureCall(f(argm, 3), mul)
    assert y == 6
    assert argm.value_a == 1
    assert argm.value_b == 2

    if choice():
        f = add
    else:
        f = mul

    @CallSlotProof(add_or_mul(f))
    def add_or_mul_proof(f: f_type) -> None:

        @UniversallyQuantified
        def uq(argm: Argument, x: int) -> None:
            Requires(Acc(argm.value_a) and Acc(argm.value_b))

            if f == add:
                y = ClosureCall(f(argm, x), add)  # type: int
            else:
                y = ClosureCall(f(argm, x), mul)

            Ensures(y == argm.value_a + x or y == argm.value_b * x)

    y1 = ClosureCall(f(argm, 3), add_or_mul(f)(argm, 3))  # type: int
    y2 = ClosureCall(f(argm, 3), add_or_mul(f)(argm, 3))  # type: int
    assert y1 == 4 or y2 == 6
    assert y1 == y2
    assert argm.value_a == 1
    assert argm.value_b == 2
    assert y1 == ClosureCall(f(argm, 3), add_or_mul(f)(argm, 3))

    @CallSlotProof(hof_slot(f))
    def hof_slot_proof(f: f_type) -> None:

        @UniversallyQuantified
        def uq(argm: Argument, x: int) -> None:
            Requires(Acc(argm.value_a) and Acc(argm.value_b))

            if f == add:
                y = ClosureCall(f(argm, x), add)  # type: int
            else:
                y = ClosureCall(f(argm, x), mul)

            Ensures(y <= argm.value_a + x or y >= argm.value_b * x)

    h = hof
    y = ClosureCall(h(f, argm), hof)
    assert y <= 6 or y >= 10
    assert argm.value_a == 1
    assert argm.value_b == 2
