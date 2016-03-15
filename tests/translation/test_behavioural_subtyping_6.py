from py2viper_contracts.contracts import *


class Super:
    def some_function(self, a: int) -> int:
        Requires(a >= 0)
        Ensures(Result() > 17)
        return 18 + a


class Sub(Super):
    #:: ExpectedOutput(invalid.program:invalid.override)
    @Pure
    def some_function(self, c: int) -> int:
        Requires(True)
        Ensures(Result() > 17)
        return 19
