from py2viper_contracts.contracts import (
    Invariant,
)
from py2viper_contracts.io import *


def test(t: Place) -> None:
    while True:
        #:: ExpectedOutput(invalid.program:obligation.fresh.in_loop)
        Invariant(token(t))
