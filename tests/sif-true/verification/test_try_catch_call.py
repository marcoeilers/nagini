# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class MyZeroDivException(Exception):
    pass

def divide(n: int, d: int) -> int:
    Ensures(Implies(Low(n) and Low(d), Low(Result())))
    Ensures(d != 0 and Result() == n // d)
    Exsures(MyZeroDivException, d == 0)
    if d != 0:
        return n // d
    else:
        raise MyZeroDivException()

def m1(x: int, y: int) -> int:
    Requires(Low(x) and Low(y))
    Ensures(Low(Result()))
    Ensures(Implies(y == 0, Result() == 0))
    Ensures(Implies(y != 0, Result() == x // y))
    try:
        return divide(x, y)
    except MyZeroDivException:
        return 0

def m2(x: int) -> None:
    Requires(x > 0)
    Ensures(False)
    Exsures(MyZeroDivException, True)
    while True:
        divide(10, x)
        x -= 1

def raiseOnZero(x: int) -> None:
    Ensures(x != 0)
    Exsures(Exception, x == 0)
    if x == 0:
        raise Exception()

def m3(secret: int) -> int:
    Ensures(Low(Result()))
    r = 34
    try:
        raiseOnZero(secret)
    except Exception as e:
        r = 35
    finally:
        r = 36
    return r
