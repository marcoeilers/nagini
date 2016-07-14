from py2viper_contracts.contracts import *


@Predicate
def P(i: int) -> bool:
    return i == 2


@Pure
def a_function() -> bool:
    return True