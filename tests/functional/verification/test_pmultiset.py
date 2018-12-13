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
