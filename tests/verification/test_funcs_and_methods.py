from contracts.contracts import *

@Pure
def func1(b : int) -> int:
    Requires(b == 15)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 32)
    return b + 16

@Pure
def func3(x : int, y : int, z : bool) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == (x != y))
    return x == y and (y == x or x == x)


def func2(arg : int) -> int:
    Ensures(Result() == 48 - 6)
    arg2 = arg
    while arg2 > 0:
        Invariant(True)
        localvar12 = False
        arg2 -= 5
    if localvar12 and localvar12:
        localvar = func1(15)
        return localvar + 10
    else:
        return 42