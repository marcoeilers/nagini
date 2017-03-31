from nagini_contracts.contracts import *


class SomeClass:
    #:: ExpectedOutput(invalid.program:invalid.predicate)
    @Predicate
    def meh(self, val: int) -> int:
        return val