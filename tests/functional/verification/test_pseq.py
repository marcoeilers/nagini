# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    pass


def test_seq() -> None:
    no_ints = PSeq()  # type: PSeq[int]
    Assert(len(no_ints) == 0)
    ints = PSeq(1, 2, 3)
    a = A()
    ass = PSeq(a)
    Assert(a in ass)
    Assert(3 in ints and 1 in ints)
    Assert(4 not in ints)
    Assert(ass[0] is a)
    Assert(ints[1] == 2)
    Assert(len(ints) == 3)
    ints2 = ints + ints
    Assert(len(ints2) == 6)
    Assert(ints2[3] == 1)
    ints3 = ints2.take(4)
    Assert(len(ints3) == 4)
    Assert(ints3[1] == ints2[1])
    ints4 = ints.update(0, 3)
    Assert(1 not in ints4)
    Assert(ints4[0] == 3)
    ints5 = ints.drop(2)
    Assert(len(ints5) == 1)
    Assert(ints5[0] == 3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def test_list_ToSeq() -> None:
    a = [1,2,3]
    Assert(ToSeq(a) == PSeq(1,2,3))
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def test_dict_ToSeq() -> None:
    a = {1: 45, 2: 34}
    b = ToSeq(a)
    Assert(1 in b)
    Assert(2 in b)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(3 in b)


def test_set_ToSeq() -> None:
    a = {1, 3, 5}
    b = ToSeq(a)
    Assert(1 in b)
    Assert(5 in b)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(2 in b)