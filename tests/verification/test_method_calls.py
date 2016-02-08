from contracts.contracts import *


class Class1:
    def __init__(self) -> None:
        Ensures(Acc(self.c2) and isinstance(self.c2, Class2))  # type: ignore
        Ensures(Acc(self.c2.c1) and self.c2.c1 == self)  # type: ignore
        self.c2 = Class2(self)

    @Pure
    def getc2(self) -> 'Class2':
        Requires(Acc(self.c2))  # type: ignore
        return self.c2

    def getc2impure(self) -> 'Class2':
        Requires(Acc(self.c2))  # type: ignore
        Ensures(Acc(self.c2))  # type: ignore
        Ensures(self.c2 == Old(self.c2))
        Ensures(Result() == self.c2)  # type: ignore
        return self.c2

    def setc2(self, c2: 'Class2') -> None:
        Requires(Acc(self.c2))
        Ensures(Acc(self.c2))
        Ensures(self.c2 == c2)
        self.c2 = c2


class Class2:
    def __init__(self, c1: Class1) -> None:
        Ensures(Acc(self.c1) and self.c1 == c1)  # type: ignore
        self.c1 = c1

    @Pure
    def getc1(self) -> Class1:
        Requires(Acc(self.c1))  # type: ignore
        return self.c1

    def getc1impure(self) -> Class1:
        Requires(Acc(self.c1))  # type: ignore
        Ensures(Acc(self.c1))  # type: ignore
        Ensures(self.c1 == Old(self.c1))
        Ensures(Result() == self.c1)  # type: ignore
        return self.c1

    def setc1(self, c1: Class1) -> None:
        Requires(Acc(self.c1))
        Ensures(Acc(self.c1))
        Ensures(self.c1 == c1)
        self.c1 = c1


def chainedcalls() -> None:
    c1 = Class1()
    c2 = c1.getc2().c1.getc2().getc1impure().c2.getc1().getc2impure().getc1().c2.getc1impure().c2
    Assert(c1 == c2.c1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c1 == c2)


def nestedcalls() -> None:
    c1_1 = Class1()
    c1_2 = Class1()
    c1_2.getc2().setc1(c1_1.getc2impure().c1)
    Assert(c1_2.c2.c1 == c1_1)


@Pure
def id(c1: Class1) -> Class1:
    return c1


def nestedcalls2() -> None:
    c1_1 = Class1()
    c1_2 = Class1()
    c1_2.getc2().setc1(c1_1.c2.getc1impure())
    c1_1.getc2().getc1().c2.setc1(id(c1_2))
    Assert(c1_2.c2.c1 == c1_1)
    Assert(c1_1.c2.c1.c2.c1 == c1_1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c1_1.c2.c1 == c1_1)
