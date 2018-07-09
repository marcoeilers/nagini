from nagini_contracts.contracts import *

class Container:
    def __init__(self) -> None:
        self.f = 0
        Ensures(Acc(self.f))

@Predicate
def contPred(c: Container) -> bool:
    return Acc(c.f)

@AllLow
def inc(c: Container) -> None:
    Requires(Acc(c.f))
    Ensures(Acc(c.f))
    Ensures(c.f == Old(c.f) + 1)
    c.f = c.f + 1

@AllLow
def incPred(c: Container) -> None:
    Requires(contPred(c))
    Ensures(contPred(c))
    Ensures(Unfolding(contPred(c), c.f == Old(Unfolding(contPred(c), c.f)) + 1))
    Unfold(contPred(c))
    c.f = c.f + 1
    Fold(contPred(c))

@AllLow
def low_m(a: int) -> int:
    return a + 1

def foo(secret: bool, c: Container) -> None:
    Requires(Acc(c.f))
    Requires(Low(c.f))
    Ensures(Acc(c.f))
    Ensures(Low(c.f))
    if secret:
        x = 1 # do something
    inc(c)
