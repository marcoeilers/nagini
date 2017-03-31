from nagini_contracts.contracts import *

class A:

    def first(self) -> int:
        #:: ExpectedOutput(invalid.program:recursive.static.call)
        return A.second(self)

    def second(self) -> int:
        return A.first(self)