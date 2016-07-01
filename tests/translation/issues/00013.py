from py2viper_contracts.contracts import *


@Predicate
def foo(x: int) -> bool:
    #:: ExpectedOutput(invalid.program:contract.outside.function)
    Requires(x == 5)
    return True
