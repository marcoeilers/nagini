from nagini_contracts.contracts import *

def foo() -> int:
    Ensures(Result() > 3)
    return 4