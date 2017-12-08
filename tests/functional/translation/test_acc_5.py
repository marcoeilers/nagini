from nagini_contracts.contracts import *

x = 2
x = 4

def m() -> int:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Acc(x)
    return 12
