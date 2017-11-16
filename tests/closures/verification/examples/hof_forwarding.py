from typing import Callable
from nagini_contracts.contracts import (
    Implies,
    Requires,
    Ensures,
    Result,
    Old,
    Invariant,
    Predicate,
    Fold,
    Unfold,
    Unfolding,
    Acc,
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
)


def inc(x: int) -> int:
    Ensures(Result() == x + 1)
    return x + 1


def mul(x: int) -> int:
    Requires(x > 0)
    Ensures(Result() == x * 2)
    return x * 2


@Predicate
def pre(x: int, pre_token: int) -> bool:
    return (
        True if pre_token == 1 else
        x > 0 if pre_token == 2 else
        True
    )


@Predicate
def post(x: int, ret: int, post_token: int) -> bool:
    return (
        ret == x + 1 if post_token == 1 else
        ret == x * 2 if post_token == 2 else
        True
    )


f0_type = Callable[[int], int]


@CallSlot
def f1_slot(f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
    Requires(pre(x, pre_token))
    ret = f0(x)
    Ensures(post(x, ret, post_token))


def f1(f0: f0_type, x: int, pre_token: int, post_token: int) -> int:
    Requires(f1_slot(f0, x, pre_token, post_token))
    Requires(pre(x, pre_token))
    Ensures(post(x, Result(), post_token))
    return ClosureCall(f0(x), f1_slot(f0, x, pre_token, post_token)())


f1_type = Callable[[f0_type, int, int, int], int]


@CallSlot
def f2_slot(f1: f1_type, f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
    Requires(pre(x, pre_token))
    ret = f1(f0, x, pre_token, post_token)
    Ensures(post(x, ret, post_token))


def f2(f1: f1_type, f0: f0_type, x: int, pre_token: int, post_token: int) -> int:
    Requires(f2_slot(f1, f0, x, pre_token, post_token))
    Requires(pre(x, pre_token))
    Ensures(post(x, Result(), post_token))
    return ClosureCall(
        f1(f0, x, pre_token, post_token),
        f2_slot(f1, f0, x, pre_token, post_token)()
    )


f2_type = Callable[[f1_type, f0_type, int, int, int], int]


@CallSlot
def f3_slot(f2: f2_type, f1: f1_type, f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
    Requires(pre(x, pre_token))
    ret = f2(f1, f0, x, pre_token, post_token)
    Ensures(post(x, ret, post_token))


def f3(f2: f2_type, f1: f1_type, f0: f0_type, x: int, pre_token: int, post_token: int) -> int:
    Requires(f3_slot(f2, f1, f0, x, pre_token, post_token))
    Requires(pre(x, pre_token))
    Ensures(post(x, Result(), post_token))
    return ClosureCall(
        f2(f1, f0, x, pre_token, post_token),
        f3_slot(f2, f1, f0, x, pre_token, post_token)()
    )


def client() -> None:

    _inc = inc
    _mul = mul

    _f1 = f1
    _f2 = f2
    _f3 = f3

    @CallSlotProof(f1_slot(_inc, 5, 1, 1))
    def f1_slot_inc(f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
        Requires(pre(x, pre_token))
        Unfold(pre(x, pre_token))
        ret = ClosureCall(f0(x), inc)  # type: int
        Fold(post(x, ret, post_token))
        Ensures(post(x, ret, post_token))

    @CallSlotProof(f2_slot(_f1, _inc, 5, 1, 1))
    def f2_slot_inc(_f1: f1_type, _f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
        Requires(pre(x, pre_token))

        ret = ClosureCall(_f1(_f0, x, pre_token, post_token), f1)  # type: int

        Ensures(post(x, ret, post_token))

    @CallSlotProof(f3_slot(_f2, _f1, _inc, 5, 1, 1))
    def f3_slot_inc(_f2: f2_type, _f1: f1_type, _f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
        Requires(pre(x, pre_token))

        ret = ClosureCall(_f2(_f1, _f0, x, pre_token, post_token), f2)  # type: int

        Ensures(post(x, ret, post_token))

    Fold(pre(5, 1))
    y1 = ClosureCall(_f3(_f2, _f1, _inc, 5, 1, 1), f3)  # type: int
    Unfold(post(5, y1, 1))
    assert y1 == 6

    @CallSlotProof(f1_slot(_mul, 5, 2, 2))
    def f1_slot_mul(f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
        Requires(pre(x, pre_token))
        Unfold(pre(x, pre_token))
        ret = ClosureCall(f0(x), mul)  # type: int
        Fold(post(x, ret, post_token))
        Ensures(post(x, ret, post_token))

    @CallSlotProof(f2_slot(_f1, _mul, 5, 2, 2))
    def f2_slot_mul(_f1: f1_type, _f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
        Requires(pre(x, pre_token))

        ret = ClosureCall(_f1(_f0, x, pre_token, post_token), f1)  # type: int

        Ensures(post(x, ret, post_token))

    @CallSlotProof(f3_slot(_f2, _f1, _mul, 5, 2, 2))
    def f3_slot_mul(_f2: f2_type, _f1: f1_type, _f0: f0_type, x: int, pre_token: int, post_token: int) -> None:
        Requires(pre(x, pre_token))

        ret = ClosureCall(_f2(_f1, _f0, x, pre_token, post_token), f2)  # type: int

        Ensures(post(x, ret, post_token))

    Fold(pre(5, 2))
    y2 = ClosureCall(_f3(_f2, _f1, _mul, 5, 2, 2), f3)  # type: int
    Unfold(post(5, y2, 2))
    assert y2 == 10
