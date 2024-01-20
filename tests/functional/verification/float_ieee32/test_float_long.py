# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(158)
# Ignore this file because it non-deterministically takes very long.

from nagini_contracts.contracts import *

def useOps(f: float, g: float) -> float:
    a = f - g
    b = f * g
    c = f > g
    d = f >= g
    e = f < g
    e2 = f <= g
    asd = 1 / 2
    return f

def specialVals() -> None:
    nan = float("nan")
    nf = float("inF")
    one = float("1.0")
    Assert(nf > one)
    Assert(not nan == nan)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(nan == nan)


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
