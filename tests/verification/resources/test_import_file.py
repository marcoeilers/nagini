from py2viper_contracts.contracts import *

@Pure
def test_func() -> bool:
    return True

def test_method(a: int) -> int:
    Ensures(Result() >= 0)
    Ensures(Implies(a > 0, Result() < a))
    Ensures(Implies(a <= 0, Result() == 0))
    return 17 # it shouldn't matter that this one is incorrect