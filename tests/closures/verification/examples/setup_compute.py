from typing import Callable, Optional
from nagini_contracts.contracts import (
    Requires,
    Ensures,
    Acc,
    Predicate,
    Fold,
    Unfold,
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
)


class Argument:

    def __init__(self, a: int, b: int) -> None:
        self.a = a  # type: int
        self.b = b  # type: int

        Ensures(Acc(self.a) and Acc(self.b))
        Ensures(self.a == a and self.b == b)


F_Type = Callable[[Argument, int], Optional[object]]


@CallSlot
def f_setup(setup: F_Type, c: int, d: int, before_token: int, between_token: int) -> None:

    @UniversallyQuantified
    def uq(arg: Argument) -> None:
        Requires(before(arg, c, d, before_token))

        setup(arg, c)

        Ensures(between(arg, c, d, between_token))


@CallSlot
def f_compute(compute: F_Type, c: int, d: int, between_token: int, after_token: int) -> None:

    @UniversallyQuantified
    def uq(arg: Argument) -> None:
        Requires(between(arg, c, d, between_token))

        compute(arg, d)

        Ensures(after(arg, c, d, after_token))


def f(
        setup: F_Type,
        compute: F_Type,
        arg: Argument,
        c: int,
        d: int,
        before_token: int,
        between_token: int,
        after_token: int
) -> None:

    Requires(f_setup(setup, c, d, before_token, between_token))
    Requires(f_compute(compute, c, d, between_token, after_token))
    Requires(before(arg, c, d, before_token))

    ClosureCall(setup(arg, c), f_setup(setup, c, d, before_token, between_token)(arg))

    # assert between(arg, c, d, between_token)

    ClosureCall(compute(arg, d), f_compute(compute, c, d, between_token, after_token)(arg))

    Ensures(after(arg, c, d, after_token))


def setup(arg: Argument, c: int) -> Optional[object]:
    Requires(Acc(arg.a))
    Requires(c > 1)
    Ensures(Acc(arg.a))
    Ensures(arg.a == 3 * c)

    arg.a = 3 * c


def compute(arg: Argument, d: int) -> Optional[object]:
    Requires(Acc(arg.a, 1 / 2) and Acc(arg.b))
    Ensures(Acc(arg.a, 1 / 2) and Acc(arg.b))
    Ensures(arg.b == arg.a + d)

    arg.b = arg.a + d


@Predicate
def before(arg: Argument, c: int, d: int, token: int) -> bool:
    return (
        Acc(arg.a) and Acc(arg.b) and c > 1 if token == 1 else
        True
    )


@Predicate
def between(arg: Argument, c: int, d: int, token: int) -> bool:
    return (
        Acc(arg.b) and Acc(arg.a) and arg.a == 3 * c if token == 1 else
        True
    )


@Predicate
def after(arg: Argument, c: int, d: int, token: int) -> bool:
    return (
        Acc(arg.a) and Acc(arg.b) and arg.a == 3 * c and arg.b == arg.a + d if token == 1 else
        True
    )


def client() -> None:

    arg = Argument(2, 2)
    c, d = 2, 3
    before_token = between_token = after_token = 1

    @CallSlotProof(f_setup(setup, c, d, before_token, between_token))
    def f_setup_proof(f: F_Type, c: int, d: int, A: int, B: int) -> None:

        @UniversallyQuantified
        def uq(arg: Argument) -> None:
            Requires(before(arg, c, d, before_token))
            Unfold(before(arg, c, d, between_token))

            ClosureCall(f(arg, c), setup)

            Fold(between(arg, c, d, between_token))
            Ensures(between(arg, c, d, between_token))

    @CallSlotProof(f_compute(compute, c, d, between_token, after_token))
    def f_compute_proof(f: F_Type, c: int, d: int, B: int, C: int) -> None:

        @UniversallyQuantified
        def uq(arg: Argument) -> None:
            Requires(between(arg, c, d, between_token))
            Unfold(between(arg, c, d, between_token))

            ClosureCall(f(arg, d), compute)

            Fold(after(arg, c, d, after_token))
            Ensures(after(arg, c, d, after_token))

    Fold(before(arg, c, d, between_token))
    f(setup, compute, arg, c, d, before_token, between_token, after_token)
    Unfold(after(arg, c, d, after_token))

    assert arg.a == 6
    assert arg.b == 9
