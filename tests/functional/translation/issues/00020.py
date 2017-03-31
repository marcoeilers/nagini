from nagini_contracts.contracts import *

x = 4

#:: ExpectedOutput(invalid.program:multiple.definitions)
x = 5

def bla() -> None:
    Requires(True)
    Ensures(x == 5)
    pass
