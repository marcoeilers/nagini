from py2viper_contracts.contracts import Requires
from py2viper_contracts.io import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def test(t1: Place) -> None:
    #:: ExpectedOutput(invalid.program:invalid.io_operation_use.open_basic_io_operation)
    Open(read_int_io(t1))
