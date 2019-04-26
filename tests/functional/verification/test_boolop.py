# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


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


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.value) and self.value == 0)  # type: ignore
        self.value = 0


class A:
    def test(self, c: Container) -> None:
        Requires(Acc(c.value))
        Ensures(Acc(c.value) and c.value == 5)
        c.value = 5


class B(A):
    pass


class C(A):
    pass


class D():
    def __init__(self) -> None:
        Requires(False)


class E():
    def __init__(self, c: Container) -> None:
        Requires(Acc(c.value))
        Ensures(Acc(c.value) and c.value == Old(c.value) + 5)
        c.value += 5


def m_type() -> None:
    c = Container()
    (B() or C()).test(c)
    assert c.value == 5


def m_type_2() -> A:
    c = Container()
    return B() and C()


def m_type_f() -> None:
    c = Container()
    (B() or C()).test(c)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def m_type_2_f() -> A:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    c = Container()
    return B() and C()


def m_stmt_or() -> None:
    c = Container()
    a = E(c) or D()
    assert c.value == 5


def m_stmt_or_2() -> None:
    c = Container()
    l = []  # type: List[int]
    #:: ExpectedOutput(call.precondition:assertion.false)
    a = l or D()


def m_stmt_and() -> None:
    c = Container()
    #:: ExpectedOutput(call.precondition:assertion.false)
    a = E(c) and D()


def m_stmt_and_2() -> None:
    c = Container()
    a = E(c) and E(c)
    assert c.value == 10


def m_stmt_and_3() -> None:
    c = Container()
    l = []  # type: List[int]
    a = l and E(c)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c.value == 5