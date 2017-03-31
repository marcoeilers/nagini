from nagini_contracts.contracts import *


def foo() -> None:
    while True:
        a = True
        #:: ExpectedOutput(invalid.program:invalid.contract.position)
        Invariant(a)
