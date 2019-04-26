# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class SomeClass:
    def __init__(self) -> None:
        Ensures(Acc(self.field)) # type: ignore
        self.field = 14

    #:: ExpectedOutput(invalid.program:invalid.predicate)
    @Predicate
    def meh(self, val: int) -> bool:
        a = self.field == val
        return Acc(self.field) and a