from py2viper_contracts.contracts import (
    Requires,
)
from py2viper_contracts.io import *


def test(t: Place) -> None:
    #:: ExpectedOutput(invalid.program:obligation.fresh.in_precondition)
    Requires(token(t))
