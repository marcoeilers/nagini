from py2viper_contracts.contracts import *


@Pure
def f1(i: int) -> int:
    a = i + 67
    return a - 34
    #:: ExpectedOutput(type.error:dead.code)
    b = 5678
    return 23
