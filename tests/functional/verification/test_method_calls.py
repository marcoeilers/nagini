# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Class1:
    def __init__(self) -> None:
        Ensures(Acc(self.c2) and isinstance(self.c2, Class2))  # type: ignore
        Ensures(Acc(self.c2.c1) and self.c2.c1 is self)  # type: ignore
        self.c2 = Class2(self)

    @Pure
    def get_c2(self) -> 'Class2':
        Requires(Acc(self.c2))  # type: ignore
        return self.c2

    def get_c2_impure(self) -> 'Class2':
        Requires(Acc(self.c2))  # type: ignore
        Ensures(Acc(self.c2))  # type: ignore
        Ensures(self.c2 is Old(self.c2))
        Ensures(Result() is self.c2)  # type: ignore
        return self.c2

    def set_c2(self, c2: 'Class2') -> None:
        Requires(Acc(self.c2))
        Ensures(Acc(self.c2))
        Ensures(self.c2 is c2)
        self.c2 = c2


class Class2:
    def __init__(self, c1: Class1) -> None:
        Ensures(Acc(self.c1) and self.c1 is c1)  # type: ignore
        self.c1 = c1

    @Pure
    def get_c1(self) -> Class1:
        Requires(Acc(self.c1))  # type: ignore
        return self.c1

    def get_c1_impure(self) -> Class1:
        Requires(Acc(self.c1))  # type: ignore
        Ensures(Acc(self.c1))  # type: ignore
        Ensures(self.c1 is Old(self.c1))
        Ensures(Result() is self.c1)  # type: ignore
        return self.c1

    def set_c1(self, c1: Class1) -> None:
        Requires(Acc(self.c1))
        Ensures(Acc(self.c1))
        Ensures(self.c1 is c1)
        self.c1 = c1


def chained_calls() -> None:
    c1 = Class1()
    c2 = c1.get_c2().c1.get_c2().get_c1_impure().c2.get_c1().get_c2_impure().get_c1().c2.get_c1_impure().c2
    Assert(c1 == c2.c1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c1 == c2)


def nested_calls() -> None:
    c1_1 = Class1()
    c1_2 = Class1()
    c1_2.get_c2().set_c1(c1_1.get_c2_impure().c1)
    Assert(c1_2.c2.c1 == c1_1)


@Pure
def id(c1: Class1) -> Class1:
    return c1


def nested_calls2() -> None:
    c1_1 = Class1()
    c1_2 = Class1()
    c1_2.get_c2().set_c1(c1_1.c2.get_c1_impure())
    c1_1.get_c2().get_c1().c2.set_c1(id(c1_2))
    Assert(c1_2.c2.c1 == c1_1)
    Assert(c1_1.c2.c1.c2.c1 == c1_1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c1_1.c2.c1 == c1_1)


def null_test(b: bool) -> None:
    c1 = Class1()
    c2 = c1 if b else None
    c1.get_c2_impure()
    #:: ExpectedOutput(call.precondition:assertion.false)
    c2.get_c2_impure()


def null_test_pure(b: bool) -> None:
    c1 = Class1()
    c2 = c1 if b else None
    c1.get_c2()
    #:: ExpectedOutput(application.precondition:assertion.false)
    c2.get_c2()
