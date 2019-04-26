# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Super:
    pass


def test_constr() -> None:
    super1 = Super()
    super5 = Super()
    super6 = Super()
    myset = {super1, super5, super6}
    empty_set = set() # type: Set[Super]


def test_constr_arg() -> None:
    l = [1,2,3]
    s = set(l)
    assert 3 in s
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 5 in s


def test_in() -> None:
    super1 = Super()
    super5 = Super()
    super6 = Super()
    super8 = Super()
    super55 = Super()
    myset = {super1, super5, super6}
    empty_set = set() # type: Set[Super]
    Assert(super1 in myset)
    Assert(super6 in myset)
    Assert(not (super8 in myset))
    Assert(not (super1 in empty_set))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(55 in myset)


def test_add() -> None:
    super1 = Super()
    super5 = Super()
    super6 = Super()
    super8 = Super()
    super17 = Super()
    super34 = Super()
    super36 = Super()
    super987 = Super()
    myset = {super1, super5, super6}
    empty_set = set() # type: Set[Super]
    Assert(not (super8 in myset))
    myset.add(super8)
    Assert(super8 in myset)
    Assert(super1 in myset)
    Assert(not (super17 in myset))
    empty_set.add(super34)
    Assert(super34 in empty_set)
    Assert(not (super36 in empty_set))
    empty_set.add(super987)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(not (super987 in empty_set))


def test_clear() -> None:
    super1 = Super()
    super5 = Super()
    super6 = Super()
    super17 = Super()
    super55 = Super()
    myset = {super1, super5, super6}
    empty_set = set() # type: Set[Super]
    empty_set.add(super55)
    myset.clear()
    Assert(not (super1 in myset))
    Assert(not (super17 in myset))
    Assert(super55 in empty_set)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(super5 in myset)
