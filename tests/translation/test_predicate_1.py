from contracts.contracts import *


#:: ExpectedOutput(invalid.program:invalid.predicate)
@Predicate
def meh(val: int) -> int:
    return val