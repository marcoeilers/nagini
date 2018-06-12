from nagini_contracts.contracts import *

def static_foo() -> int:
    Requires(LowEvent())
    Ensures(Low(Result()))
    return 0

class A:
    def dynamic_foo(self) -> None:
        Requires(LowEvent())

    def dynamic_bar(self) -> int:
        Ensures(Low(Result()))
        return 0

class B(A):
    def dynamic_foo(self) -> None:
        Requires(LowEvent())

    def dynamic_bar(self) -> int:
        Ensures(Low(Result()))
        return 1

def client1(secret: bool) -> None:
    Requires(LowEvent())
    if (secret):
        a = A()
    else:
        a = B()
    #:: ExpectedOutput(call.precondition:assertion.false)
    a.dynamic_foo()

def client2(secret: bool) -> None:
    Requires(LowEvent())
    if (secret):
        a = A()
    else:
        a = B()
    x = a.dynamic_bar()
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Low(x))
