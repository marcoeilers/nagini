from contracts.contracts import *

def m1(a: int) -> int:
    Ensures(Result() == 56)
    return 56

#:: ExpectedOutput(invalid.program:purity.violated)
GLOBAL_VAR = m1(23)