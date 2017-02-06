from py2viper_contracts.contracts import *
from typing import List


def m() -> None:
    a = [1,2,3,4,5]
    assert a[-2] == 4
    b = a[:]
    assert b[0] == 1
    assert len(b) == 5
    assert b[3] == 4
    assert ToSeq(a) == ToSeq(b)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def m2() -> None:
    a = [1,2,3,4,5]
    assert a[-2] == 4
    b = a[2:]
    assert b[0] == 3
    assert len(b) == 3
    assert b[2] == 5
    #:: ExpectedOutput(application.precondition:assertion.false)
    c = b[3]


def m3() -> None:
    a = [1,2,3,4,5]
    assert a[-2] == 4
    b = a[:3]
    assert b[0] == 1
    assert len(b) == 3
    assert b[2] == 3
    assert b[-3] == 1
    #:: ExpectedOutput(application.precondition:assertion.false)
    c = b[-4]


def m_tuple() -> None:
    a = (1,2,3,4,5)
    assert a[-2] == 4
    b = a[:]
    assert b[0] == 1
    assert len(b) == 5
    assert b[3] == 4
    assert ToSeq(a) == ToSeq(b)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def m2_tuple() -> None:
    a = (1, 2, 3, 4, 5)
    assert a[-2] == 4
    b = a[2:]
    assert b[0] == 3
    assert len(b) == 3
    assert b[2] == 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def m3_tuple() -> None:
    a = (1, 2, 3, 4, 5)
    assert a[-2] == 4
    b = a[:3]
    assert b[0] == 1
    assert len(b) == 3
    assert b[2] == 3
    assert b[-3] == 1
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False