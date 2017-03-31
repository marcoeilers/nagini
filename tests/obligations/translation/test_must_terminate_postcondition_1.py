from nagini_contracts.contracts import (
    Ensures,
)
from nagini_contracts.obligations import *


def return_termination() -> None:
    #:: ExpectedOutput(invalid.program:obligation.must_terminate.in_postcondition)
    Ensures(MustTerminate(1))
