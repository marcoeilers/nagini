# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from nagini_contracts.contracts import *


def useOps(f: float, g: float) -> float:
    a = f - g
    b = f * g
    c = f > g
    d = f >= g
    e = f < g
    e2 = f <= g
    return f


def fromString() -> None:
    one = float("1.0")
    two = float("2.0")
    Assert(two > one)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(two > two)


def cmpLits() -> None:
    Assert(3.0 > 2.0)
    Assert(1.0 <= 40.0)

def sqr(num : float) -> float:
    Requires(num >= 0)
    Ensures(Result() >= 0)
    Ensures(num * num == Result())
    return num * num


def sqr2(num : float) -> float:
    Requires(num >= 0.0)
    Ensures(Result() >= 0.0)
    Ensures(num * num == Result())
    return num * num


def sqr3(num : float) -> float:
    Requires(num >= 0.0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 0.0)
    Ensures(num * num == Result())
    return num * num

def arith(num: float) -> float:
    Requires(not isNaN(num))
    Ensures(Result() == num + 3)
    return num + 1.0 + 2.0


def arith2(num: float) -> float:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == num + 4)
    return num + 1.0 + 2.0


def intComp() -> None:
    a = 3.0
    b = 3
    Assert(a == b)

def divSave(f: float, g: float) -> float:
    #:: ExpectedOutput(application.precondition:assertion.false)
    tmp = f / g
    return 1.0

def divSave2(f: float, g: float) -> float:
    Requires(g != 0.0)
    return f / g