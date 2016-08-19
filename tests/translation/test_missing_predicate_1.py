from py2viper_contracts.contracts import *


def test() -> None:
    #:: ExpectedOutput(type.error:Name 'foo' is not defined)
    Requires(foo())
