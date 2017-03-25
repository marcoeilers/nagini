from py2viper_contracts.contracts import *


class A:
    SOME_CONST = 23
    SOME_CONST_2 = SOME_CONST + 4

    def a(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false, L1)
        Ensures(Result() > 22)
        return self.SOME_CONST

    def a_2(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false)|ExpectedOutput(postcondition.violated:assertion.false, L1)
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

#:: Label(L1)
class B(A):
    SOME_CONST = 12


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

def whatever_4() -> int:
    Ensures(Result() == 12)
    return B.SOME_CONST

def whatever_5() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 13)
    return B.SOME_CONST

def whatever_6(a: A) -> int:
    Ensures(Implies(type(a) is A, Result() == 23))
    Ensures(Implies(type(a) is B, Result() == 12))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 23)
    return a.SOME_CONST

def whatever_7(a: B) -> int:
    Ensures(Implies(type(a) is A, Result() == 23))
    Ensures(Implies(type(a) is B, Result() == 12))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 12)
    return a.SOME_CONST