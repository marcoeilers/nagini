from py2viper_contracts.contracts import *


@Predicate
def foo(x: int) -> bool:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Requires(x == 5)
    return True
