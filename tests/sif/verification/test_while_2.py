from nagini_contracts.contracts import *

def m1(x: int) -> int:
    Requires(Low(x))
    Ensures(Low(Result()))
    res = 1
    while res < x:
        Invariant(Low(res))
        res = res * 2
        if res > 100:
            return res
        res = res + 4
    return res

def m2(x: int) -> int:
    Ensures(Low(Result()))
    res = 1
    while res < x:
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(Low(res))
        res = res * 2
        if res > 100:
            return res
        res = res + 4
    return res

def m3(x: int) -> None:
    Requires(x > 0)
    i = 0
    res = 0
    while (i < x):
        Invariant(0 <= i and i <= x)
        Invariant(res == i * 2)
        i = i + 1
        res = res + 2
    Assert(res == 2 * x)

def next_leapyear(start: int) -> int:
    Requires(Low(start))
    Ensures(Low(Result()))
    Ensures(Result() > start)
    Ensures(Result() % 4 == 0)
    Ensures(Result() % 100 != 0 or Result() % 400 == 0)
    next_ly = start + 1
    while True:
        Invariant(next_ly > start)
        Invariant(Low(next_ly))
        if next_ly % 4 != 0:
            next_ly = next_ly + 1
            continue
        if next_ly % 100 == 0:
            if next_ly % 400 == 0:
                break
            else:
                next_ly = next_ly + 4
                continue
        break
    return next_ly
