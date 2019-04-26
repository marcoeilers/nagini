# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(28)
from nagini_contracts.contracts import GhostReturns
from nagini_contracts.io_contracts import *


#:: ExpectedOutput(invalid.program:decorators.incompatible)
@IOOperation
@GhostReturns(2)
def read_int_io(
        t_pre1: Place,
        res: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
