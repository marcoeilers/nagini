from nagini_contracts.contracts import *

def a() -> None:
    #:: ExpectedOutput(invalid.program:nested.function.declaration)
    def b() -> None:
        return
    return