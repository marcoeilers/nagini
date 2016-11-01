from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *
from typing import Tuple


def test() -> Place:
    IOExists1(Place)(
        lambda t2: (
        Ensures(
            t2 == Result() and
            token(t2)
        ),
        )
    )

    #:: ExpectedOutput(type.error:Name 't2' is not defined)
    a = t2
