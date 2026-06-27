# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Ensures, Result, Implies, list_pred
from typing import List


def in_bounds(l: List[int], i: int) -> int:
    Requires(list_pred(l))
    Requires(0 <= i < len(l))
    return l[i]


def transitivity_pass(a: int, b: int, c: int) -> None:
    Requires(a < b < c)
    assert a < c
    assert a < b
    assert b < c


def transitivity_fail(a: int, b: int, c: int) -> None:
    Requires(a < b < c)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a > c


def nonstrict_le_pass(a: int, b: int, c: int) -> None:
    Requires(a <= b <= c)
    assert a <= c


def nonstrict_le_fail(a: int, b: int, c: int) -> None:
    # a <= b <= c does not imply the strict a < c.
    Requires(a <= b <= c)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a < c


def four_chain_pass(a: int, b: int, c: int, d: int) -> None:
    Requires(a < b < c < d)
    assert a < d


def four_chain_fail(a: int, b: int, c: int, d: int) -> None:
    Requires(a < b < c < d)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a < c < b


def chained_eq_pass(a: int, b: int, c: int) -> bool:
    Ensures(Implies(Result(), a == c))
    return a == b == c


def chained_eq_fail(a: int, b: int, c: int) -> bool:
    # a == b == c does not hold just because a == c.
    Requires(a == c)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result())
    return a == b == c


def mixed_ops_pass(x: int) -> None:
    Requires(0 <= x <= 10)
    assert x >= 0
    assert x <= 10


def mixed_ops_fail(x: int) -> None:
    Requires(0 <= x <= 10)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert x < 10
