from nagini_contracts.contracts import *


def func(i: int) -> bool:
    return i == 0

def client() -> int:
    #:: ExpectedOutput(invalid.program:invalid.let)
    Ensures(Let(Result(), bool, func))
    return 0