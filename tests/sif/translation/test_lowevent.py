from nagini_contracts.contracts import *

def precond_ok() -> None:
    Requires(LowEvent())

def postcond_not_ok() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Ensures(LowEvent())
