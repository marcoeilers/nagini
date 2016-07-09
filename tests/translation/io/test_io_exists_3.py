from py2viper_contracts.contracts import Result
from py2viper_contracts.io import *
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
