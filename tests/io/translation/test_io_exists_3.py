# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *
from typing import Tuple


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


@IOOperation
def read_int_io2(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)
    #:: ExpectedOutput(invalid.program:invalid.io_operation.body.ioexists)
    return True and IOExists1(int)(
        lambda value: True
        )
