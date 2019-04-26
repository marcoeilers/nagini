# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Super:
    pass


def test_constr() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    super_list = [super1, super2, super3]
    empty_list = [] # type: List[Super]


def test_alternate_constr() -> None:
    a = list()  # type: List[int]
    assert len(a) == 0
    assert 6 not in a
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 2 in a


def test_constr_arg() -> None:
    l1 = [1,2,3]
    l2 = list(l1)
    assert 2 in l2
    assert l2[2] == 3
    l1[0] = 5
    assert l2[0] == 1
    l2[1] = 7
    assert l1[1] == 2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 8 in l2


def test_len() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    super_list = [super1, super2, super3]
    Assert(len(super_list) == 3)
    empty_list = [] # type: List[Super]
    Assert(len(empty_list) == 0)
    Assert(len([]) == 0)
    Assert(len([super1]) == 1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(len([super1]) == 0)

def test_in() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mylist = [super1, super2, super3]
    super4 = Super()
    Assert(super1 in mylist)
    Assert(not (super4 in mylist))
    Assert(super2 in mylist)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(super4 in mylist)

def test_subscript() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mylist = [super1, super2, super3]
    Assert(mylist[1] == super2)
    Assert(mylist[2] == super3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mylist[0] == super3)

def test_assign() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mylist = [super1, super2, super3]
    Assert(mylist[1] == super2)
    Assert(mylist[2] == super3)
    mylist[2] = mylist[0]
    Assert(mylist[1] == super2)
    Assert(mylist[2] == super1)
    Assert(len(mylist) == 3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mylist[0] == super3)

def test_append() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mylist = [super1, super2, super3]
    Assert(len(mylist) == 3)
    super4 = Super()
    Assert(not (super4 in mylist))
    mylist.append(super4)
    Assert(len(mylist) == 4)
    Assert(super4 in mylist)
    Assert(mylist[3] == super4)
    Assert(mylist[2] == super3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mylist[0] == super4)

def test_extend() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    super4 = Super()
    mylist = [super1, super2]
    mylist2 = [super3, super4]
    mylist.extend(mylist2)
    assert len(mylist) == 4
    assert len(mylist2) == 2
    assert mylist2[0] is super3
    assert mylist[0] is super1
    assert mylist[2] is super3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert super1 in mylist2


def test_add() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    super4 = Super()
    mylist = [super1, super2]
    mylist2 = [super3, super4]
    mylist3 = mylist + mylist2
    assert len(mylist) == 2
    assert len(mylist2) == 2
    assert len(mylist3) == 4
    assert mylist[0] is super1
    assert mylist2[0] is super3
    assert mylist3[0] is super1
    assert mylist3[2] is super3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert super3 in mylist


def test_mul() -> None:
    super1 = Super()
    super2 = Super()
    mylist = [super1, super2]
    newlist = mylist * 3
    assert len(mylist) == 2
    assert len(newlist) == 6
    assert mylist[0] is super1
    assert newlist[0] is super1
    assert newlist[2] is super1
    assert newlist[5] is super2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert mylist[1] is super1