#:: IgnoreFile(53)
from py2viper_contracts.contracts import (
    Exsures,
)


def callee() -> int:
    Exsures(Exception, True)
    raise Exception()


def caller() -> int:
    try:
        a = callee()
    except:
        return a
    return 5
