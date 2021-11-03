# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def m3(x: int, h: int) -> int:
    Requires(Low(x))
    Requires(x > 0)
    Ensures(Low(Result()))
    i = 0
    res = 0
    hsum = 0
    while (i < x):
        Invariant(0 <= i and i <= x)
        Invariant(res == i * 2)
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(Low(i) and Low(res))
        i = i + 1
        res = res + 2
        hsum += h
        if h > 34:
            break
    return res

def m4(x: int, h: int) -> int:
    Requires(Low(x))
    Requires(x > 0)
    Ensures(Low(Result()))
    i = 0
    res = 0
    hsum = 0
    while (i < x):
        Invariant(0 <= i and i <= x)
        Invariant(res == i * 2)
        Invariant(Low(i) and Low(res))
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(LowExit())
        i = i + 1
        res = res + 2
        hsum += h
        if h > 34:
            break
    return res
