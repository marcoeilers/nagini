from py2viper_contracts.contracts import Result
from py2viper_contracts.io import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def test(t1: Place) -> None:

    #:: ExpectedOutput(invalid.program:invalid.get_ghost_output.type_mismatch)
    t2 = GetGhostOutput(read_int_io(t1), 'result')  # type: Place
