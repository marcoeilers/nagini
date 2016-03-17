from py2viper_contracts.contracts import *


def test_constr() -> None:
    myset = {1, 5 , 6}
    empty_set = set() # type: Set[int]

def test_in() -> None:
    myset = {1, 5 , 6}
    empty_set = set() # type: Set[int]
    Assert(1 in myset)
    Assert(6 in myset)
    Assert(not (8 in myset))
    Assert(not (1 in empty_set))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(55 in myset)

def test_add() -> None:
    myset = {1, 5 , 6}
    empty_set = set() # type: Set[int]
    Assert(not (8 in myset))
    myset.add(8)
    Assert(8 in myset)
    Assert(1 in myset)
    Assert(not (17 in myset))
    empty_set.add(34)
    Assert(34 in empty_set)
    Assert(not (36 in empty_set))
    empty_set.add(987)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(not (987 in empty_set))

def test_clear() -> None:
    myset = {1, 5 , 6}
    empty_set = set() # type: Set[int]
    empty_set.add(55)
    myset.clear()
    Assert(not (1 in myset))
    Assert(not (17 in myset))
    Assert(55 in empty_set)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(5 in myset)