from py2viper_contracts.contracts import *


class Super:
    @Pure
    def some_function(self, a: int) -> int:
        return a


class Sub(Super):
    #:: ExpectedOutput(invalid.program:invalid.override)
    @Pure
    def some_function(self, a: int) -> int:
        return a
