from py2viper_contracts.contracts import *


class Super:
    def some_method(self) -> int:
        Ensures(Result() >= 14)
        return 14


class Sub(Super):
    def some_method(self) -> int:
        Ensures(Result() >= 15)
        a = self
        #:: ExpectedOutput(invalid.program:invalid.super.call)
        return 1 + super(a, Sub).some_method()