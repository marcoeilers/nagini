# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    pass


def test_pset() -> None:
    no_ints = PSet()  # type: PSet[int]
    assert len(no_ints) == 0
    ints = PSet(1, 2, 3)
    four = PSet(4)
    a = A()
    a_set = PSet(a)
    assert a in a_set
    assert 3 in ints and 1 in ints
    assert 4 not in ints
    assert len(ints) == 3
    ints2 = ints + ints
    # Viper's set axiomatization is unable to prove the next one
    # assert len(ints2) == 3
    ints3 = ints + four
    assert len(ints3) == 4
    assert 4 in ints3
    assert 4 not in ints
    assert 4 not in ints2
    assert 1 in ints
    assert 1 in ints2
    assert 1 in ints3

    ints4 = ints3 - ints
    assert len(ints4) == 1
    assert 4 in ints4
    assert 1 not in ints4

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
