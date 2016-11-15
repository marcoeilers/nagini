from py2viper_contracts.contracts import *


def test1() -> None:
    #:: ExpectedOutput(type.error:Name 'MyException' is not defined)
    raise MyException()
