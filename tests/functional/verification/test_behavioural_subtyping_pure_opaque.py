# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# Basic tests with normal conditions
class SuperA:
    def __init__(self) -> None:
        self.int_field = 14
        self.bool_field = True

    @Opaque
    @Pure
    def foo(self, b: int) -> int:
        Requires(b > 9)
        Ensures(Result() > 9)
        return b


class SubA(SuperA):
    @Opaque
    @Pure
    def foo(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 10)
        return b + 5


class SubSubA(SubA):
    @Opaque
    @Pure
    def foo(self, b: int) -> int:
        Requires(b > 3)
        Ensures(Result() > 12)
        return b + 9


class SuperB:
    @Opaque
    @Pure
    #:: Label(L1)
    def bar(self, b: int) -> int:
        Requires(b > 9)
        Ensures(Result() > 9)
        return b


class SubB(SuperB):
    @Opaque
    @Pure
    #:: ExpectedOutput(application.precondition:assertion.false,L1)|Label(L2)
    def bar(self, b: int) -> int:
        Requires(b > 10)
        Ensures(Result() > 10)
        return b + 5


class SubSubB(SubB):
    @Opaque
    @Pure
    #:: ExpectedOutput(application.precondition:assertion.false,L2)
    def bar(self, b: int) -> int:
        Requires(b > 11)
        Ensures(Result() > 10)
        return b + 5


class SuperC:
    @Opaque
    @Pure
    def foo(self, b: int) -> int:
        Requires(b > 9)
        #:: ExpectedOutput(postcondition.violated:assertion.false,L3)
        Ensures(Result() > 9)
        return b


class SubC(SuperC):
    @Opaque
    @Pure
    #:: Label(L3)
    def foo(self, b: int) -> int:
        Requires(b > 5)
        #:: ExpectedOutput(postcondition.violated:assertion.false,L4)
        Ensures(Result() > 8)
        return b + 5

 
class SubSubC(SubC):
    @Opaque
    @Pure
    #:: Label(L4)
    def foo(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 2)
        return b + 5

# Covariant return types, contravariant parameters
class SuperF:
    @Opaque
    @Pure
    def foo(self, a: SubA, b: SubSubA) -> SubA:
        return b


class SubF1(SuperF):
    @Opaque
    @Pure
    def foo(self, a: SubA, b: SubSubA) -> SubSubA:
        return b


class SubF2(SuperF):
    @Opaque
    @Pure
    def foo(self, a: SuperA, b: SubA) -> SubA:
        return b


class SuperNamed:
    def foo(self, named: int = 23) -> int:
        Ensures(Result() == named)
        return named


class SubNamed(SuperNamed):
    #:: ExpectedOutput(assert.failed:assertion.false)
    def foo(self, named: int = 56) -> int:
        Ensures(Result() == named)
        return named
