from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def test(t1: Place) -> None:

    a = 't_post'
    #:: ExpectedOutput(invalid.program:invalid.get_ghost_output.result_identifier_not_str)
    t2 = GetGhostOutput(read_int_io(t1), a)  # type: Place
