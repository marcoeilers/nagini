# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Predicate, Result
from nagini_contracts.io_contracts import *


@Predicate
@IOOperation        #:: ExpectedOutput(invalid.program:decorators.incompatible)
def read_int_io(
        t_pre1: Place,
        res: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
