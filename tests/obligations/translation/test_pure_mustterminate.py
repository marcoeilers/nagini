# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Requires,
    Pure
)
from nagini_contracts.obligations import *


@Pure
def pure_termination() -> int:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Requires(MustTerminate(1))
