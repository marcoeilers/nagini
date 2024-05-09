# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.value) and self.value == 0)  # type: ignore
        self.value = 0


def updating_id(b: bool, c: Container) -> bool:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == Old(c.value) + 1)
    Ensures(Result() == b)
    c.value += 1
    return b


def test_and(b1: bool, b2: bool) -> bool:
    Ensures(Implies(Result(), b1))
    Ensures(Implies(Result(), b2))
    c = Container()
    res = updating_id(b1, c) and updating_id(b2, c)
    Assert(Implies(b1, c.value == 2))
    Assert(Implies(not b1, c.value == 1))
    return res


def test_or(b1: bool, b2: bool) -> bool:
    Ensures(Implies(b1, Result()))
    Ensures(Implies(b2, Result()))
    c = Container()
    res = updating_id(b1, c) or updating_id(b2, c)
    Assert(Implies(not b1, c.value == 2))
    Assert(Implies(b1, c.value == 1))
    return res


def test_and_fail(b1: bool, b2: bool) -> bool:
    Ensures(Implies(Result(), b1))
    Ensures(Implies(Result(), b2))
    c = Container()
    Assert(c.value == 0)
    res = updating_id(b1, c) and updating_id(b2, c)
    Assert(c.value != 0)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c.value == 2 or c.value == 0)
    return res


def test_or_fail(b1: bool, b2: bool) -> bool:
    Ensures(Implies(b1, Result()))
    Ensures(Implies(b2, Result()))
    c = Container()
    Assert(c.value == 0)
    res = updating_id(b1, c) or updating_id(b2, c)
    Assert(c.value != 0)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c.value == 2 or c.value == 0)
    return res


def updating_id_int(b: int, c: Container) -> int:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == Old(c.value) + 1)
    Ensures(Result() == b)
    c.value += 1
    return b


def test_ternary(b: bool) -> int:
    Ensures(Implies(b, Result() == 15))
    Ensures(Implies(not b, Result() == 32))
    c1 = Container()
    c2 = Container()
    res = updating_id_int(15, c1) if updating_id(b, c1) else updating_id_int(32, c2)
    Assert(c1.value >= 1)
    Assert(Implies(b, c1.value == 2))
    Assert(Implies(b, c2.value == 0))
    Assert(Implies(not b, c1.value == 1))
    Assert(Implies(not b, c2.value == 1))
    return res


def test_ternary_fail(b: bool) -> int:
    Ensures(Implies(b, Result() == 15))
    Ensures(Implies(not b, Result() == 32))
    c1 = Container()
    c2 = Container()
    res = updating_id_int(15, c1) if updating_id(b, c1) else updating_id_int(32, c2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c1.value + c2.value != 2)
    return res

def test_mod(i: int) -> bool:
    Ensures(Implies(i == 2, Result()))
    return i % 2 == 0

def test_mod_fail(i: int) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(i == 3, Result()))
    return i % 2 == 0

def test_div(i: int) -> int:
    Ensures(Implies(i == 16 or i == 17, Result() == 8))
    return i // 2

def test_div_fail(i: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(i == 18, Result() == 8))
    return i // 2