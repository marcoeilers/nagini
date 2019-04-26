# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def static_foo() -> int:
    Requires(LowEvent())
    Ensures(Low(Result()))
    return 0


class A:
    def __init__(self) -> None:
        self.f = 0
        Fold(pred(self))
        Ensures(pred(self))

    def dynamic_foo(self) -> None:
        Requires(LowEvent())

    def dynamic_bar(self) -> int:
        Ensures(Low(Result()))
        return 0

class B(A):
    def __init__(self) -> None:
        self.f = 1
        Fold(pred(self))
        Ensures(pred(self))

    def dynamic_foo(self) -> None:
        Requires(LowEvent())

    def dynamic_bar(self) -> int:
        Ensures(Low(Result()))
        return 1

@Predicate
def pred(x: A) -> bool:
    return Acc(x.f) and Low(x.f)

def client1(secret: bool) -> None:
    Requires(LowEvent())
    if secret:
        a = A()
    else:
        a = B()
    #:: ExpectedOutput(call.precondition:assertion.false)
    a.dynamic_foo()

def client2(secret: bool) -> None:
    Requires(LowEvent())
    if secret:
        a = A()
    else:
        a = B()
    x = a.dynamic_bar()
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Low(x))

def client3(secret: bool) -> None:
    if secret:
        a = A()
    else:
        a = B()
    #:: ExpectedOutput(unfold.failed:sif.unfold)
    Unfold(pred(a))
