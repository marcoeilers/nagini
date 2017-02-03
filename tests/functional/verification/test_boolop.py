from py2viper_contracts.contracts import *


def m() -> None:
    a = 3 and 4 and 5
    assert a == 5


def m2() -> None:
    a = 3 or 4 or 5
    assert a == 3


def m3() -> None:
    empty = []  # type: List[int]
    a = 3 and empty and 5
    assert a is empty


def m4() -> None:
    empty = []  # type: List[int]
    a = 3 or empty or 5
    assert a == 3


def m5() -> None:
    empty = []  # type: List[int]
    a = empty or 4 or 5
    assert a == 4


def m_f() -> None:
    a = 3 and 4 and 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a == 4


def m2_f() -> None:
    a = 3 or 4 or 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a == 4


def m3_f() -> None:
    empty = []  # type: List[int]
    a = 3 and empty and 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a is 5


def m4_f() -> None:
    empty = []  # type: List[int]
    a = 3 or empty or 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a == 5


def m5_f() -> None:
    empty = []  # type: List[int]
    a = empty or 4 or 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a is empty

