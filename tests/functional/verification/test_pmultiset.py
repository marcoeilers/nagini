# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    pass


def test_pmultiset() -> None:
    no_ints = PMultiset()  # type: PMultiset[int]
    Assert(len(no_ints) == 0)
    ints = PMultiset(1, 2, 3, 1)
    four = PMultiset(4)
    a = A()
    a_set = PMultiset(a)
    Assert(a_set.num(a) == 1)
    Assert(ints.num(3) == 1 and ints.num(1) == 2)
    Assert(ints.num(4) == 0)
    Assert(len(ints) == 4)
    ints2 = ints + ints
    # Viper's set axiomatization is unable to prove the next one
    # assert len(ints2) == 3
    ints3 = ints + four
    Assert(len(ints3) == 5)
    Assert(ints3.num(4) == 1)
    Assert(ints.num(4) == 0)
    Assert(ints2.num(4) == 0)
    Assert(ints.num(1) == 2)
    Assert(ints2.num(1) == 4)
    Assert(ints3.num(1) == 2)

    ints4 = ints3 - ints
    Assert(len(ints4) == 1)
    Assert(ints4.num(4) == 1)
    Assert(ints4.num(1) == 0)

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def test_toMS() -> None:
    no_ints_seq = PSeq()  # type: PSeq[int]
    no_ints = ToMS(no_ints_seq)
    Assert(len(no_ints) == 0)
    ints_seq = PSeq(1, 2, 3, 1)
    ints = ToMS(ints_seq)
    a = A()
    ass_seq = PSeq(a)
    ass = ToMS(ass_seq)
    Assert(ass.num(a) == 1)
    Assert(ints.num(3) == 1 and ints.num(1) == 2)
    Assert(ints.num(4) == 0)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(ints.num(5) > 0)
