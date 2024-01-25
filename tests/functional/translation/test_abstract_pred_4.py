from nagini_contracts.contracts import *

class MyClass:
    def __init__(self) -> None:
        pass

    @Predicate
    @ContractOnly
    def huh(self) -> bool:
        return True


def huhFunc(mc: MyClass) -> int:
    Ensures(Result() > 0)
    #:: ExpectedOutput(invalid.program:abstract.predicate.fold)
    Fold(mc.huh())
    return 4
