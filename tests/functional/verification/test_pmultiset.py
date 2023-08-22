# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    pass


def test_pmultiset() -> None:
    no_ints = PMultiset()  # type: PMultiset[int]
    assert len(no_ints) == 0
    ints = PMultiset(1, 2, 3, 1)
    four = PMultiset(4)
    a = A()
    a_set = PMultiset(a)
    assert a_set.num(a) == 1
    assert ints.num(3) == 1 and ints.num(1) == 2
    assert ints.num(4) == 0
    assert len(ints) == 4
    ints2 = ints + ints
    # Viper's set axiomatization is unable to prove the next one
    # assert len(ints2) == 3
    ints3 = ints + four
    assert len(ints3) == 5
    assert ints3.num(4) == 1
    assert ints.num(4) == 0
    assert ints2.num(4) == 0
    assert ints.num(1) == 2
    assert ints2.num(1) == 4
    assert ints3.num(1) == 2

    ints4 = ints3 - ints
    assert len(ints4) == 1
    assert ints4.num(4) == 1
    assert ints4.num(1) == 0

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def test_toMS() -> None:
    no_ints_seq = PSeq()  # type: PSeq[int]
    no_ints = ToMS(no_ints_seq)
    assert len(no_ints) == 0
    ints_seq = PSeq(1, 2, 3, 1)
    ints = ToMS(ints_seq)
    a = A()
    ass_seq = PSeq(a)
    ass = ToMS(ass_seq)
    assert ass.num(a) == 1
    assert ints.num(3) == 1 and ints.num(1) == 2
    assert ints.num(4) == 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert ints.num(5) > 0
