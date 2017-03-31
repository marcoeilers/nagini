from nagini_contracts.contracts import *


class TestClass:

    def __init__(self) -> None:
        Ensures(Acc(self.fld)) # type: ignore
        self.fld = 14

    def some_func(self) -> int:
        Requires(Acc(self.fld, 1/100))
        return self.fld

    @Predicate
    def some_pred(self, val: int) -> bool:
        #:: ExpectedOutput(invalid.program:not_expression)
        return Acc(self.fld) and self.some_func() == val
