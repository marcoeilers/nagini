from nagini_contracts.contracts import *

x = 2
x = 4

def m() -> int:
    Ensures(Result() == 2)
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Requires(x == 2)
    return 2
