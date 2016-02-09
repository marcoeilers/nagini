from contracts.contracts import *


# Basic tests with normal conditions
class SuperA:
    def __init__(self) -> None:
        self.intfield = 14
        self.boolfield = True

    def somemethod(self, a: int) -> int:
        Requires(a > 9)
        Ensures(Result() > 9)
        return a


class SubA(SuperA):
    def somemethod(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 10)
        return b + 5


class SubSubA(SubA):
    def somemethod(self, b: int) -> int:
        Requires(b > 3)
        Ensures(Result() > 12)
        return b + 9


class SuperB:
    def somemethod(self, a: int) -> int:
        Requires(a > 9)
        Ensures(Result() > 9)
        return a


class SubB(SuperB):
    #:: ExpectedOutput(call.precondition:assertion.false)
    def somemethod(self, b: int) -> int:
        Requires(b > 10)
        Ensures(Result() > 10)
        return b + 5


class SubSubB(SubB):
    #:: ExpectedOutput(call.precondition:assertion.false)
    def somemethod(self, b: int) -> int:
        Requires(b > 11)
        Ensures(Result() > 10)
        return b + 5


class SuperC:
    def somemethod(self, a: int) -> int:
        Requires(a > 9)
        Ensures(Result() > 9)
        return a


class SubC(SuperC):
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def somemethod(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 8)
        return b + 5


class SubSubC(SubC):
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def somemethod(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 2)
        return b + 5


# Basic tests with access permissions
class SuperD:
    def somemethod(self, a: SuperA) -> int:
        Requires(Acc(a.intfield, 1 / 2))
        Ensures(Acc(a.intfield, 1 / 4))
        return a.intfield


class SubD(SuperD):
    def somemethod(self, b: SuperA) -> int:
        Requires(Acc(b.intfield, 1 / 2))
        Ensures(Acc(b.intfield, 1 / 4))
        return b.intfield + 5


class SubD2(SuperD):
    def somemethod(self, b: SuperA) -> int:
        Requires(Acc(b.intfield, 1 / 4))
        Ensures(Acc(b.intfield, 1 / 4))
        return b.intfield + 5


class SubD3(SuperD):
    def somemethod(self, b: SuperA) -> int:
        Requires(Acc(b.intfield, 1 / 2))
        Ensures(Acc(b.intfield, 1 / 2))
        return b.intfield + 5


class SuperE:
    def somemethod(self, a: SuperA) -> int:
        Requires(Acc(a.intfield, 1 / 2))
        Ensures(Acc(a.intfield, 1 / 4))
        return a.intfield


class SubE(SuperE):
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    def somemethod(self, b: SuperA) -> int:
        Requires(Acc(b.intfield, 2 / 3))
        Ensures(Acc(b.intfield, 2 / 3))
        return b.intfield + 5


class SubE2(SuperE):
    #:: ExpectedOutput(postcondition.violated:insufficient.permission)
    def somemethod(self, b: SuperA) -> int:
        Requires(Acc(b.intfield, 1 / 2))
        Ensures(Acc(b.intfield, 1 / 8))
        return b.intfield + 5


class SubE3(SuperE):
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    def somemethod(self, b: SuperA) -> int:
        Requires(Acc(b.boolfield, 1 / 2))
        Ensures(Acc(b.boolfield, 1 / 2))
        return 5


# Covariant return types, contravariant parameters
class SuperF:
    def somemethod(self, b: SubA, a: SubSubA) -> SubA:
        return a


class SubF1(SuperF):
    def somemethod(self, a: SubA, b: SubSubA) -> SubSubA:
        return b


class SubF2(SuperF):
    def somemethod(self, a: SuperA, b: SubA) -> SubA:
        return b


# Declared exceptions
class MyException(Exception):
    pass


class MySpecialException(MyException):
    pass


class MyOtherException(Exception):
    pass


class Super:
    def somefunction(self, a: int) -> int:
        Requires(a >= 0)
        Ensures(Result() > 17)
        Exsures(MyException, True)
        return 18 + a


class Sub(Super):
    def somefunction(self, c: int) -> int:
        Requires(True)
        Ensures(Result() > 17)
        Exsures(MySpecialException, True)
        Exsures(MyException, True)
        return 19

        # TODO test if exceptional postconditions coincide
