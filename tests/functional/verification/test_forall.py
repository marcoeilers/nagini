from nagini_contracts.contracts import *


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


def test_dict_values() -> None:
    r = {3 : 7, 4: 8,5: 9}
    Assert(Forall(r.values(), lambda i: (i > 5, [])))


def test_dict_values_2() -> None:
    r = {3: 7, 4: 8, 5: 9}
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(r.values(), lambda i: (i > 7, [])))
