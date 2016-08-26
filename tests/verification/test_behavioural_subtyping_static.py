from py2viper_contracts.contracts import *


class A:
    @staticmethod
    def static_method() -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false,L1)
        Ensures(Result() > 1)
        return 17


class B(A):
    @staticmethod
    def static_method() -> int:
        Ensures(Result() > 6)
        return 66


class C(A):
    @staticmethod
    def static_method() -> int:
        #:: Label(L1)
        Ensures(Result() > 0)
        return 666
