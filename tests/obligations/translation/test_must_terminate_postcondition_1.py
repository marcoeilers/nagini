# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Ensures,
)
from nagini_contracts.obligations import *


def return_termination() -> None:
    #:: ExpectedOutput(invalid.program:obligation.must_terminate.in_postcondition)
    Ensures(MustTerminate(1))
