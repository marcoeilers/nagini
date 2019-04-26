# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Super:
    pass


def test_dict_constr() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7: super3}
    empty_dict = {} # type: Dict[int, Super]


def test_dict_in() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7: super3}
    empty_dict = {} # type: Dict[int, Super]
    Assert(1 in mydict)
    Assert(not (1 in empty_dict))
    Assert(7 in mydict)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(4 in mydict)


def test_dict_subscript() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7: super3}
    empty_dict = {} # type: Dict[int, Super]
    Assert(mydict[1] == super1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mydict[7] == super2)


def test_dict_get() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7: super3}
    empty_dict = {} # type: Dict[int, Super]
    Assert(mydict.get(1) == super1)
    Assert(mydict.get(7) == super3)
    Assert(mydict.get(44) == None)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(empty_dict.get(45) == super2)


def test_dict_values() -> None:
    mydict = {1: 1, 7: 3}
    empty_dict = {}  # type: Dict[int, int]
    Assert(not (4 in empty_dict))
    empty_dict[4] = 2
    Assert(4 in empty_dict)
    Assert(empty_dict[4] == 2)
    Assert(mydict[1] == 1)
    Assert(not (1 in empty_dict))
    mydict[1] = 3
    Assert(mydict[1] == 3)
    Assert(1 in mydict)
    Assert(mydict[7] == 3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mydict[1] == 1)


def list_test() -> None:
    mylist = [1, 2, 3]
    Assert(len(mylist) == 3)
    Assert(not (4 in mylist))
    mylist.append(4)
    Assert(len(mylist) == 4)
    Assert(4 in mylist)
    Assert(mylist[3] == 4)
    Assert(mylist[2] == 3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mylist[0] == 4)


def test_set_constr() -> None:
    myset = {1, 5 , 6}
    empty_set = set() # type: Set[int]


def test_set_in() -> None:
    myset = {1, 5 , 6}
    empty_set = set() # type: Set[int]
    Assert(1 in myset)
    Assert(6 in myset)
    Assert(not (8 in myset))
    Assert(not (1 in empty_set))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(55 in myset)


def test_set_add() -> None:
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


def test_set_clear() -> None:
    myset = {1, 5, 6}
    empty_set = set() # type: Set[int]
    empty_set.add(55)
    myset.clear()
    Assert(not (1 in myset))
    Assert(not (17 in myset))
    Assert(55 in empty_set)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(5 in myset)
