from nagini_contracts.contracts import *

def m1(x: int) -> int:
    Requires(x > 0)
    i = 0
    sum = 0
    while(i < x):
        Invariant(0 <= x and x <= x)
        sum += i
        i += 1
    return sum

def m2(x: int) -> int:
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

def next_leapyear(start: int) -> int:
    Ensures(Result() > start)
    Ensures(Result() % 4 == 0)
    Ensures(Result() % 100 != 0 or Result() % 400 == 0)

    next_ly = start + 1
    while True:
        Invariant(next_ly > start)

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
