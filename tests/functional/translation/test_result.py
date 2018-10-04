from nagini_contracts.contracts import *


def noreturn() -> None:
    #:: ExpectedOutput(invalid.program:invalid.result)
    Ensures(Result() is None)
    pass