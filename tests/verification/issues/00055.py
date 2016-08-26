from py2viper_contracts.contracts import (
    Assert,
)


def test() -> None:
    try:
        x = 5
    except OSError as ex1:
        x = 6
        try:
            x = 7
        except OverflowError as ex2:
            Assert(isinstance(ex1, OSError))
