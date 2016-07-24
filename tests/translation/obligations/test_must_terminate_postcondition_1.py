from py2viper_contracts.contracts import (
    Ensures,
)
from py2viper_contracts.obligations import *


def return_termination() -> None:
    #:: ExpectedOutput(invalid.program:obligation.must_terminate.in_postcondition)
    Ensures(MustTerminate(1))
