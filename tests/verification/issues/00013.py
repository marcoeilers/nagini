#:: IgnoreFile(/py2viper/issue/13/)
from py2viper_contracts.contracts import *

@Predicate
def foo(x: int) -> bool:
    Requires(x == 5)
    return True
