from py2viper_contracts.io import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def test(t1: Place) -> None:

    #:: ExpectedOutput(invalid.program:invalid.get_ghost_output.invalid_result_identifier)
    t2 = GetGhostOutput(read_int_io(t1), 't_pre')  # type: Place
