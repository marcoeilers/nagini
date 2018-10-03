from nagini_contracts.contracts import *

class Container:
    def __init__(self, x: int) -> None:
        self.f = x

@Pure
def getF(x: Container) -> int:
    Requires(Acc(x.f))
    return x.f

def m1(x: Container) -> int:
    Requires(Acc(x.f))
    Ensures(Result() == 12)
    x.f = 12
    return getF(x)

def m2(x: Container) -> int:
    Requires(Acc(x.f))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    return getF(x)

def m3(x: Container) -> int:
    Requires(Acc(x.f))
    Requires(Low(x.f))
    Ensures(Low(Result()))
    return getF(x)
