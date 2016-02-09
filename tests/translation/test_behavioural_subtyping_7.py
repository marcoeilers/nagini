from contracts.contracts import *


class Super:
    @Pure
    def somefunction(self, a: int) -> int:
        Requires(a >= 0)
        Ensures(Result() > 17)
        return 18 + a


class Sub(Super):
    #:: ExpectedOutput(invalid.program:invalid.override)
    def somefunction(self, c: int) -> int:
        Requires(True)
        Ensures(Result() > 17)
        return 19
