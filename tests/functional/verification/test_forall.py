# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import TypeVar, Generic, Dict


def test_range() -> None:
    r = range(3, 6)
    Assert(Forall(r, lambda i: i > 1))


def test_range_2() -> None:
    r = range(3, 6)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(r, lambda i: i > 4))


def test_list() -> None:
    r = [3,4,5]
    Assert(Forall(r, lambda i: (i > 1, [])))


def test_list_2() -> None:
    r = [3,4,5]
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(r, lambda i: (i > 4, [])))


def test_set() -> None:
    r = {3,4,5}
    Assert(Forall(r, lambda i: (i > 1, [])))


def test_set_2() -> None:
    r = {3,4,5}
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(r, lambda i: (i > 4, [])))


def test_dict() -> None:
    r = {3 : 7, 4: 8,5: 9}
    Assert(Forall(r, lambda i: (i > 1, [])))


def test_dict_2() -> None:
    r = {3: 7, 4: 8, 5: 9}
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(r, lambda i: (i > 4, [])))


def test_type_quantification() -> None:
    r = [3, 4, 5]
    Assert(Forall(int, lambda i: Implies(i >= 0 and i < len(r), r[i] > 1)))


def test_type_quantification_2() -> None:
    r = [3, 4, 5]
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(int, lambda i: Implies(i >= 0 and i < len(r), r[i] > 3)))


T = TypeVar("T")
U = TypeVar("U")


class Gen(Generic[T, U]):

    def __init__(self, v: T, u: U) -> None:
        self.val = v
        self.val2 = u
        Ensures(Acc(self.val) and self.val is v)
        Ensures(Acc(self.val2) and self.val2 is u)


def test_type_quantification_n() -> None:
    r = [[3, 4, 5], [4, 5, 6]]
    Assert(Forall2(int, int, lambda i, j: (Implies(i >= 0 and i < len(r) and j >= 0 and j < 3, r[i][j] > 1), [[r[i][j]]])))


def test_type_quantification_n_fail(d: Dict[str, str], s: str) -> None:
    Requires(dict_pred(d))
    Requires(s in d and d[s] == s)
    gentest = Gen(True, 15)
    l1 = [3, 4, 5]
    r = [l1, [4, 5, 6]]
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall2(int, int, lambda i, j: (Implies(i >= 0 and i < len(r) and j >= 0 and j < 3, r[i][j] > 3), [[r[i][j]]])))
