from nagini_contracts.contracts import *

@Predicate
def pred1() -> bool:
    return True

@Predicate
def pred2() -> bool:
    return True

def crash() -> None:
    #:: ExpectedOutput(invalid.program:impure.disjunction)
    Requires(pred1() or pred2())
