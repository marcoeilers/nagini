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

def divSave(f: float, g: float) -> None:
    #:: ExpectedOutput(application.precondition:assertion.false)
    tmp = f / g

def divSave2(f: float, g: float) -> float:
    Requires(g != 0.0)
    return f / g
