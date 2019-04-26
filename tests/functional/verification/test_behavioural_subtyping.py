# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# Basic tests with normal conditions
class SuperA:
    def __init__(self) -> None:
        self.int_field = 14
        self.bool_field = True

    def some_method(self, b: int) -> int:
        Requires(b > 9)
        Ensures(Result() > 9)
        return b


class SubA(SuperA):
    def some_method(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 10)
        return b + 5


class SubSubA(SubA):
    def some_method(self, b: int) -> int:
        Requires(b > 3)
        Ensures(Result() > 12)
        return b + 9


class SuperB:
    #:: Label(L1)
    def some_method(self, b: int) -> int:
        Requires(b > 9)
        Ensures(Result() > 9)
        return b


class SubB(SuperB):
    #:: ExpectedOutput(call.precondition:assertion.false, L1)|Label(L2)
    def some_method(self, b: int) -> int:
        Requires(b > 10)
        Ensures(Result() > 10)
        return b + 5


class SubSubB(SubB):
    #:: ExpectedOutput(call.precondition:assertion.false, L2)
    def some_method(self, b: int) -> int:
        Requires(b > 11)
        Ensures(Result() > 10)
        return b + 5


class SuperC:
    def some_method(self, b: int) -> int:
        Requires(b > 9)
        #:: ExpectedOutput(postcondition.violated:assertion.false, L3)
        Ensures(Result() > 9)
        return b


class SubC(SuperC):
    #:: Label(L3)
    def some_method(self, b: int) -> int:
        Requires(b > 5)
        #:: ExpectedOutput(postcondition.violated:assertion.false, L4)
        Ensures(Result() > 8)
        return b + 5


class SubSubC(SubC):
    #:: Label(L4)
    def some_method(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 2)
        return b + 5


# Basic tests with access permissions
class SuperD:
    def some_method(self, b: SuperA) -> int:
        Requires(Acc(b.int_field, 1 / 2))
        Ensures(Acc(b.int_field, 1 / 4))
        return b.int_field


class SubD(SuperD):
    def some_method(self, b: SuperA) -> int:
        Requires(Acc(b.int_field, 1 / 2))
        Ensures(Acc(b.int_field, 1 / 4))
        return b.int_field + 5


class SubD2(SuperD):
    def some_method(self, b: SuperA) -> int:
        Requires(Acc(b.int_field, 1 / 4))
        Ensures(Acc(b.int_field, 1 / 4))
        return b.int_field + 5


class SubD3(SuperD):
    def some_method(self, b: SuperA) -> int:
        Requires(Acc(b.int_field, 1 / 2))
        Ensures(Acc(b.int_field, 1 / 2))
        return b.int_field + 5


class SuperE:
    #:: Label(L5)
    def some_method(self, a: SuperA) -> int:
        Requires(Acc(a.int_field, 1 / 2))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission, L6)
        Ensures(Acc(a.int_field, 1 / 4))
        return a.int_field


class SubE(SuperE):
    #:: ExpectedOutput(call.precondition:insufficient.permission, L5)
    def some_method(self, a: SuperA) -> int:
        Requires(Acc(a.int_field, 2 / 3))
        Ensures(Acc(a.int_field, 2 / 3))
        return a.int_field + 5


class SubE2(SuperE):
    #:: Label(L6)
    def some_method(self, a: SuperA) -> int:
        Requires(Acc(a.int_field, 1 / 2))
        Ensures(Acc(a.int_field, 1 / 8))
        return a.int_field + 5


class SubE3(SuperE):
    #:: ExpectedOutput(call.precondition:insufficient.permission, L5)
    def some_method(self, a: SuperA) -> int:
        Requires(Acc(a.bool_field, 1 / 2))
        Ensures(Acc(a.bool_field, 1 / 2))
        return 5


# Covariant return types, contravariant parameters
class SuperF:
    def some_method(self, a: SubA, b: SubSubA) -> SubA:
        return b


class SubF1(SuperF):
    def some_method(self, a: SubA, b: SubSubA) -> SubSubA:
        return b


class SubF2(SuperF):
    def some_method(self, a: SuperA, b: SubA) -> SubA:
        return b


# Declared exceptions
class MyException(Exception):
    pass


class MySpecialException(MyException):
    pass


class MyOtherException(Exception):
    pass


class Super:
    def some_function(self, a: int) -> int:
        Requires(a >= 0)
        Ensures(Result() > 17)
        Exsures(MyException, True)
        return 18 + a


class Sub(Super):
    def some_function(self, a: int) -> int:
        Requires(True)
        Ensures(Result() > 17)
        Exsures(MySpecialException, True)
        Exsures(MyException, True)
        return 19

# TODO test if exceptional postconditions coincide


class SuperNamed:
    def some_method(self, named: int=23) -> int:
        Ensures(Result() == named)
        return named


class SubNamed(SuperNamed):
    #:: ExpectedOutput(assert.failed:assertion.false)
    def some_method(self, named: int=56) -> int:
        Ensures(Result() == named)
        return named
