# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
@Opaque
def plusFour(i: int) -> int:
    Ensures(Result() > i)
    return i + 4

def client1() -> None:
    a = plusFour(2)
    Assert(a > 2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(a > 3)

def client2() -> None:
    a = Reveal(plusFour(2))
    Assert(a > 2)
    Assert(a > 3)
    Assert(a == 6)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(a > 7)

@Pure
def plusFiveA(i: int) -> int:
    Ensures(Result() > i + 1)
    return plusFour(i) + 1

@Pure
def plusFiveB(i: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == i + 5)
    return plusFour(i) + 1

@Pure
def plusFiveC(i: int) -> int:
    Ensures(Result() == i + 5)
    return Reveal(plusFour(i)) + 1


class MyClass:
    @Pure
    @Opaque
    def plusFour(self, i: int) -> int:
        Ensures(Result() > i)
        return i + 4

    def client1(self) -> None:
        a = self.plusFour(2)
        Assert(a > 2)
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(a > 3)

    def client2(self) -> None:
        a = Reveal(self.plusFour(2))
        Assert(a > 2)
        Assert(a > 3)
        Assert(a == 6)
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(a > 7)