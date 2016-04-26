from py2viper_contracts.contracts import *


def m1(a: int) -> int:
    return 56


@Pure
def f1(b: int) -> int:
    #:: ExpectedOutput(invalid.program:purity.violated)
    a = m1(b)
    return a + 56
