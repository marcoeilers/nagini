# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Result
from nagini_contracts.io_contracts import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def test(t1: Place) -> None:
    IOExists2(Place, int)(
        lambda t2, value: (
        Requires(
            token(t1, 1) and
            #:: ExpectedOutput(invalid.program:invalid.io_operation_use.not_variable_in_result_position)
            read_int_io(t1, 2, t2)
        ),
        )
    )
