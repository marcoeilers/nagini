# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Dict


class Super:
    pass


class Key:
    pass


def test_constr() -> None:
    key1 = Key()
    key7 = Key()
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {key1: super1, key7: super3}
    empty_dict = {} # type: Dict[Key, Super]


def test_in() -> None:
    key1 = Key()
    key7 = Key()
    key4 = Key()
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {key1: super1, key7: super3}
    empty_dict = {} # type: Dict[Key, Super]
    Assert(key1 in mydict)
    Assert(not (key1 in empty_dict))
    Assert(key7 in mydict)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(key4 in mydict)


def test_subscript() -> None:
    key1 = Key()
    key7 = Key()
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {key1: super1, key7: super3}
    empty_dict = {} # type: Dict[Key, Super]
    Assert(mydict[key1] == super1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mydict[key7] == super2)


def test_get() -> None:
    key1 = Key()
    key7 = Key()
    key44 = Key()
    key45 = Key()
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {key1: super1, key7: super3}
    empty_dict = {} # type: Dict[Key, Super]
    Assert(mydict.get(key1) == super1)
    Assert(mydict.get(key7) == super3)
    Assert(mydict.get(key44) == None)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(empty_dict.get(key45) == super2)


def test_set() -> None:
    key1 = Key()
    key7 = Key()
    key4 = Key()
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {key1: super1, key7: super3}
    empty_dict = {} # type: Dict[Key, Super]
    Assert(not (key4 in empty_dict))
    empty_dict[key4] = super2
    Assert(key4 in empty_dict)
    Assert(empty_dict[key4] == super2)
    Assert(mydict[key1] == super1)
    Assert(not (key1 in empty_dict))
    mydict[key1] = super3
    Assert(mydict[key1] == super3)
    Assert(key1 in mydict)
    Assert(mydict[key7] == super3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mydict[key1] == super1)


def test_change() -> None:
    o2: object = {1: 2}
    a = {1 : 2}
    a[2] = 4
    a[2] = 5
    assert a[2] == 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a[2] == 4
    assert False
