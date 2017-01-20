from py2viper_contracts.contracts import *


class A:
    pass


def test_seq() -> None:
    ints = Sequence(1, 2, 3)
    a = A()
    ass = Sequence(a)
    assert a in ass
    assert 3 in ints and 1 in ints
    assert 4 not in ints
    assert ass[0] is a
    assert ints[1] == 2
    assert len(ints) == 3
    ints2 = ints + ints
    assert len(ints2) == 6
    assert ints2[3] == 1
    ints3 = ints2.take(4)
    assert len(ints3) == 4
    assert ints3[1] == ints2[1]
    ints4 = ints.update(0, 3)
    assert 1 not in ints4
    assert ints4[0] == 3
    ints5 = ints.drop(2)
    assert len(ints5) == 1
    assert ints5[0] == 3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def test_list_to_seq() -> None:
    a = [1,2,3]
    assert to_seq(a) == Sequence(1,2,3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def test_dict_to_seq() -> None:
    a = {1: 45, 2: 34}
    b = to_seq(a)
    assert 1 in b
    assert 2 in b
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 3 in b


def test_set_to_seq() -> None:
    a = {1, 3, 5}
    b = to_seq(a)
    assert 1 in b
    assert 5 in b
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 2 in b