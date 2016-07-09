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

    #:: ExpectedOutput(invalid.program:invalid.get_ghost_output.argument_not_io_operation)
    t3 = GetGhostOutput(read_int_io(t1) and True, 't_post')  # type: Place
