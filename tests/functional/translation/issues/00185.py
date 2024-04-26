from nagini_contracts.contracts import *

def crash() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Invariant(True)