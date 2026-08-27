# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    pass


def test_pset() -> None:
    no_ints = PSet()  # type: PSet[int]
    Assert(len(no_ints) == 0)
    ints = PSet(1, 2, 3)
    four = PSet(4)
    a = A()
    a_set = PSet(a)
    Assert(a in a_set)
    Assert(3 in ints and 1 in ints)
    Assert(4 not in ints)
    Assert(len(ints) == 3)
    ints2 = ints + ints
    # Viper's set axiomatization is unable to prove the next one
    # assert len(ints2) == 3
    ints3 = ints + four
    Assert(len(ints3) == 4)
    Assert(4 in ints3)
    Assert(4 not in ints)
    Assert(4 not in ints2)
    Assert(1 in ints)
    Assert(1 in ints2)
    Assert(1 in ints3)

    ints4 = ints3 - ints
    Assert(len(ints4) == 1)
    Assert(4 in ints4)
    Assert(1 not in ints4)

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
