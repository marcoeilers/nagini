# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class TestClass:

    def __init__(self) -> None:
        Ensures(Acc(self.fld)) # type: ignore
        self.fld = 14

    def some_func(self) -> int:
        Requires(Acc(self.fld, 1/100))
        return self.fld

    #:: ExpectedOutput(invalid.program:invalid.predicate)
    @Predicate
    def some_pred(self, val: int) -> bool:
        return Acc(self.fld) and self.some_func() == val
