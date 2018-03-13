from nagini_contracts.contracts import *


def bla(x: int) -> None:
    Requires(True)
    Ensures(x == 5)


#:: ExpectedOutput(type.error:Name 'bla' already defined)
def bla(u: int, b: str) -> None:
    return
