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
