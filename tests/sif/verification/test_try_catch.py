from nagini_contracts.contracts import *

class MyException(Exception):
    pass

class MyException2(Exception):
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

class Container():
    def __init__(self) -> None:
        Ensures(Acc(self.value))  # type: ignore
        self.value = 0

def m4(b: bool, c: Container) -> None:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == 0)
    Exsures(MyException, Acc(c.value) and c.value == -1)
    try:
        if b:
            raise MyException()
    except MyException:
        c.value = -1
        raise MyException()
    c.value = 0

def m5(b: bool, c: Container) -> None:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == 0)
    Exsures(MyException, Acc(c.value) and c.value == -1)
    try:
        if b:
            raise MyException()
    except MyException:
        c.value = 0
    else:
        c.value = -1
        raise MyException()

def m6(i: int, c: Container) -> None:
    Requires(Low(i))
    Requires(Acc(c.value))
    Ensures(Acc(c.value))
    Ensures(Low(c.value))
    Ensures(Implies(i == 0, c.value == 0))
    Ensures(Implies(i < 0, c.value == -1))
    Ensures(Implies(i > 0, c.value == 1))
    try:
        if i < 0:
            raise MyException()
        elif i > 0:
            raise MyException2()
        else:
            c.value = 0
    except MyException:
        c.value = -1
    except MyException2:
        c.value = 1
