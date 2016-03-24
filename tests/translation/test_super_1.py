# TODO invalid super call, i.e. not super(class, self) or class is not superclass or one arg
from py2viper_contracts.contracts import *


class Super:
    def some_method(self) -> int:
        Ensures(Result() >= 14)
        return 14


class Sub(Super):
    def some_method(self) -> int:
        Ensures(Result() >= 15)
        #:: ExpectedOutput(invalid.program:invalid.super.call)
        return 1 + super(self).some_method()