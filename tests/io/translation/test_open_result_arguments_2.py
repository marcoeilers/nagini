# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *


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
    return read_int_io(t_pre, result, t_post)


def test(t1: Place) -> None:

    #:: ExpectedOutput(invalid.program:invalid.io_operation_use.result_used_argument)
    Open(read_int_io2(t1, 1))
