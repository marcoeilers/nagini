from nagini_contracts.contracts import *


#:: ExpectedOutput(invalid.program:invalid.predicate)
@Predicate
def foo(x: int) -> bool:
    Requires(x == 5)
    return True
