# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(carbon)(158)

from nagini_contracts.contracts import *

def useOps(f: float, g: float) -> float:
    a = f - g
    b = f * g
    c = f > g
    d = f >= g
    e = f < g
    e2 = f <= g
    return f


def cmpLits() -> None:
    Assert(3.0 > 2.0)
    Assert(1.0 <= 40.0)

def sqr3(num : float) -> float:
    Requires(num >= 0.0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 0.0)
    Ensures(num * num == Result())
    return num * num

def arith(num: float) -> float:
    Requires(num == num)  # not NaN
    Ensures(Result() == num + 3.0)
    tmp = 1.0 + 2.0
    return num + tmp


def arith3(num: float) -> float:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == num + 3.0)
    return num + 3.0


def arith2(num: float) -> float:
    Requires(num == num)  # not NaN
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == num + 4.0)
    return num + 1.0 + 2.0


def intComp() -> None:
    a = 3.0
    b = 3
    #:: UnexpectedOutput(assert.failed:assertion.false,158)
    Assert(a == b)

def divSave(f: float, g: float) -> float:
    #:: ExpectedOutput(application.precondition:assertion.false)
    return f / g

def divSave2(f: float, g: float) -> float:
    Requires(g != 0.0)
    return f / g
