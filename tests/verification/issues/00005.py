from py2viper_contracts.contracts import *


@Pure
def foo(a: int) -> int:
    Ensures(Implies(a > 3, Result() == a + 44))
    Ensures(Implies(a <= 3, Result() == 0))
    b = 2
    if a + b > 5:
        c = a + b
        return c + 42
    return 0
