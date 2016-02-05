from contracts.contracts import *

class Super:
    def someFunction(self, a: int) -> int:
        Requires(a >= 0)
        Ensures(Result() > 17)
        return 18 + a

class Sub(Super):
    #:: ExpectedOutput(invalid.program:invalid.override)
    @Pure
    def someFunction(self, c: int) -> int:
        Requires(True)
        Ensures(Result() > 17)
        return 19