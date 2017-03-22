from py2viper_contracts.contracts import *


class A:
    SOME_CONST = 23
    SOME_CONST_2 = SOME_CONST + 4

    def a(self) -> int:
        Ensures(Result() > 22)
        return self.SOME_CONST

    def a_2(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Result() > 24)
        return self.SOME_CONST

    @staticmethod
    def something() -> int:
        Ensures(Result() >= OTHER_CONST + 3)
        return A.SOME_CONST_2

    @staticmethod
    def something_else() -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Result() > OTHER_CONST)
        return A.SOME_CONST


OTHER_CONST = A.SOME_CONST


def whatever(b: bool) -> int:
    Ensures(Result() > OTHER_CONST - 1)
    if b:
        return A.something()
    else:
        a = A()
        return a.something()


def whatever_2(b: bool) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() <= OTHER_CONST)
    a = A()
    return a.something()


def whatever_3(b: bool) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() <= OTHER_CONST)
    return A.something()
