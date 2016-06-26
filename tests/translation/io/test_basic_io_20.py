from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *
from typing import Tuple, Callable


def test() -> Place:
    IOExists = lambda t2: (
        Ensures(
            t2 == Result() and
            token(t2)
        )
    )   # type: Callable[[Place], bool]

    #:: ExpectedOutput(type.error:Name 't2' is not defined)
    a = t2
