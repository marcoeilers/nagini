from nagini_contracts.contracts import *

class MyClass:
    def __init__(self) -> None:
        pass

@Predicate
@ContractOnly
def huh(mc: MyClass) -> bool:
    return True

def huhFunc(mc: MyClass) -> int:
    Requires(huh(mc))
    Ensures(Result() > 0)
    #:: ExpectedOutput(invalid.program:abstract.predicate.fold)
    Unfold(huh(mc))
    return 3
