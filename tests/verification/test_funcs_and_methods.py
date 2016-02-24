from contracts.contracts import *


@Pure
def func1(b: int) -> int:
    Requires(b == 15)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 32)
    a = 16
    return b + a

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
    while arg2 > 0:
        Invariant(True)
        local_var12 = False
        arg2 -= 5
    if local_var12 and local_var12:
        local_var = func1(15)
        return local_var + 10
    else:
        return 42

