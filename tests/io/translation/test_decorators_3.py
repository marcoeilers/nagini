# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Pure, Result
from nagini_contracts.io_contracts import *


@Pure
@IOOperation        #:: ExpectedOutput(invalid.program:decorators.incompatible)
def read_int_io(
        t_pre1: Place,
        res: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
