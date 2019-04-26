# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def func1(b: int) -> int:
    Requires(b == 15)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 32)
    a = 16
    return b + a

@Pure
def func1_correct(b: int) -> int:
    Requires(b == 15)
    Ensures(Result() == 32)
    return 32

def method1(b: int) -> int:
    Requires(b == 15)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 32)
    a = 16
    return b + a


@Pure
def func3(x: int, y: int, z: bool) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == (x != y))
    eq = x == y
    something = (y == x or x == x)
    return eq and something


def func2(arg: int) -> int:
    Ensures(Result() == 48 - 6)
    arg2 = arg
    local_var12 = True
    while arg2 > 0:
        Invariant(True)
        local_var12 = False
        arg2 -= 5
    if local_var12 and local_var12:
        local_var = func1_correct(15)
        return local_var + 10
    else:
        return 42

@Pure
def func(b: int, c: int) -> int:
    Ensures(Implies(b > 2, Result() == b))
    Ensures(Implies((b <= 2 and b + c > 2) and b + c <= 4, Result() == b + c + 4))
    Ensures(Implies(b <= 2 and b + c > 4, Result() == b + c + 6))
    if b > 2:
        return b
    a = b + c
    if a > 2:
        a = a + 2
        a = a + 2
    tmp = 8
    tmp -= 6
    if a > 8:
        a = a + tmp
    return a

@Pure
def func_wrong(b: int, c: int) -> int:
    Ensures(Implies(b > 2, Result() == b))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(b <= 2 and b + c > 2, Result() == b + c + 6))
    if b > 2:
        return b
    a = b + c
    if a > 2:
        a = a + 2
        a = a + 2
    if a > 8:
        a = a + 2
    return a

@Pure
def func_2(b: int, c: int) -> int:
    Ensures(Implies(b > 2, Result() == b))
    Ensures(Implies((b <= 2 and b + c > 2) and b + c <= 4, Result() == b + c + 4))
    Ensures(Implies(b <= 2 and b + c > 4, Result() == b + c + 6))
    a = b + c - 13
    if b > 2:
        return b
    else:
        a = a + 13
    tmp = 1
    tmp *= 2
    if a > 2:
        a = a + 2
        a = a + tmp
    if a > 8:
        a = a + 2
    return a

@Pure
def func_2_wrong(b: int, c: int) -> int:
    Ensures(Implies(b > 2, Result() == b))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(b <= 2 and b + c > 2, Result() == b + c + 6))
    a = b + c - 13
    if b > 2:
        return b
    else:
        a += 13
    a = b + c
    if a > 2:
        a = a + 2
        a = a + 2
    if a > 8:
        a = a + 2
    return a

