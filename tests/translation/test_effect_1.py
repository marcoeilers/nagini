from py2viper_contracts.contracts import *


@Pure
def f1(i: int) -> int:
    return 87


def m1() -> int:
    #:: ExpectedOutput(invalid.program:no.effect)
    f1(45)
    return 22
