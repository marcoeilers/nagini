from nagini_contracts.contracts import *

class MyException(Exception):
    pass

def m1(b: bool) -> int:
    Ensures(Implies(b, Result() == -2))
    Ensures(Implies(not b, Result() == 2))
    try:
        if b:
            raise MyException()
    except MyException:
        x = -1
    else:
        x = 1
    finally:
        x = 2 * x
    return x

def m2(b: bool) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(b, Result() == -2))
    Ensures(Implies(not b, Result() == 2))
    try:
        if b:
            raise MyException()
    except MyException:
        x = -2
    else:
        x = 1
    finally:
        x = 2 * x
    return x

def m3(b: bool) -> int:
    Ensures(Implies(b, Result() == -2))
    Ensures(Implies(not b, Result() == 0))
    x = 0
    try:
        if b:
            raise MyException()
    except MyException:
        x = -1
    finally:
        x = 2 * x
    return x
