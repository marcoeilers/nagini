from nagini_contracts.contracts import *

class Example:
    def __init__(self) -> None:
        self.f = 0
        Ensures(Acc(self.f))
        Ensures(self.f == 0)

class StringContainer:
    def __init__(self, s: str) -> None:
        self.s = s
        Ensures(Acc(self.s))
        Ensures(self.s == s)

def m1(secret: bool) -> Example:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(LowVal(Result()))
    a = Example()
    b = Example()
    if secret:
        return a
    return b

def m2(secret: bool) -> int:
    Ensures(Low(Result()))
    if secret:
        return 1
    return 1

def m3(secret: bool, x: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(Low(x), Low(Result())))
    if secret:
        return x + 0
    return x

def m4(secret: bool, x: int) -> int:
    Ensures(Implies(Low(x), LowVal(Result())))
    if secret:
        return x + 0
    return x

def m5(secret: bool, x: str) -> str:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(Low(x), Low(Result())))
    a = StringContainer(x)
    b = StringContainer(x)
    if secret:
        return a.s
    return b.s

def m6(secret: bool, x: str) -> str:
    Ensures(Implies(Low(x), LowVal(Result())))
    a = StringContainer(x)
    b = StringContainer(x)
    if secret:
        return a.s
    return b.s

