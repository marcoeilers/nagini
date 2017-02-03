from py2viper_contracts.contracts import *


class A:
    @staticmethod
    def static_method(a: A) -> int:
        return 17


class B(A):
    #:: ExpectedOutput(invalid.program:invalid.override)
    @staticmethod
    def static_method() -> int:
        return 17
