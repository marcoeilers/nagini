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
    def uq(argm: Argument) -> None:
        Requires(before(argm, c, d, before_token))

        setup(argm, c)

        Ensures(between(argm, c, d, between_token))


@CallSlot
def f_compute(compute: F_Type, c: int, d: int, between_token: int, after_token: int) -> None:

    @UniversallyQuantified
    def uq(argm: Argument) -> None:
        Requires(between(argm, c, d, between_token))

        compute(argm, d)

        Ensures(after(argm, c, d, after_token))


def f(
        setup: F_Type,
        compute: F_Type,
        argm: Argument,
        c: int,
        d: int,
        before_token: int,
        between_token: int,
        after_token: int
) -> None:

    Requires(f_setup(setup, c, d, before_token, between_token))
    Requires(f_compute(compute, c, d, between_token, after_token))
    Requires(before(argm, c, d, before_token))

    ClosureCall(setup(argm, c), f_setup(setup, c, d, before_token, between_token)(argm))

    # assert between(arg, c, d, between_token)

    ClosureCall(compute(argm, d), f_compute(compute, c, d, between_token, after_token)(argm))

    Ensures(after(argm, c, d, after_token))


def setup(argm: Argument, c: int) -> Optional[object]:
    Requires(Acc(argm.a))
    Requires(c > 1)
    Ensures(Acc(argm.a))
    Ensures(argm.a == 3 * c)

    argm.a = 3 * c


def compute(argm: Argument, d: int) -> Optional[object]:
    Requires(Acc(argm.a, 1 / 2) and Acc(argm.b))
    Ensures(Acc(argm.a, 1 / 2) and Acc(argm.b))
    Ensures(argm.b == argm.a + d)

    argm.b = argm.a + d


@Predicate
def before(argm: Argument, c: int, d: int, token: int) -> bool:
    return (
        Acc(argm.a) and Acc(argm.b) and c > 1 if token == 1 else
        True
    )


@Predicate
def between(argm: Argument, c: int, d: int, token: int) -> bool:
    return (
        Acc(argm.b) and Acc(argm.a) and argm.a == 3 * c if token == 1 else
        True
    )


@Predicate
def after(argm: Argument, c: int, d: int, token: int) -> bool:
    return (
        Acc(argm.a) and Acc(argm.b) and argm.a == 3 * c and argm.b == argm.a + d if token == 1 else
        True
    )


def client() -> None:

    argm = Argument(2, 2)
    c, d = 2, 3
    before_token = between_token = after_token = 1

    @CallSlotProof(f_setup(setup, c, d, before_token, between_token))
    def f_setup_proof(f: F_Type, c: int, d: int, A: int, B: int) -> None:

        @UniversallyQuantified
        def uq(argm: Argument) -> None:
            Requires(before(argm, c, d, before_token))
            Unfold(before(argm, c, d, between_token))

            ClosureCall(f(argm, c), setup)

            Fold(between(argm, c, d, between_token))
            Ensures(between(argm, c, d, between_token))

    @CallSlotProof(f_compute(compute, c, d, between_token, after_token))
    def f_compute_proof(f: F_Type, c: int, d: int, B: int, C: int) -> None:

        @UniversallyQuantified
        def uq(argm: Argument) -> None:
            Requires(between(argm, c, d, between_token))
            Unfold(between(argm, c, d, between_token))

            ClosureCall(f(argm, d), compute)

            Fold(after(argm, c, d, after_token))
            Ensures(after(argm, c, d, after_token))

    Fold(before(argm, c, d, between_token))
    f(setup, compute, argm, c, d, before_token, between_token, after_token)
    Unfold(after(argm, c, d, after_token))

    assert argm.a == 6
    assert argm.b == 9
