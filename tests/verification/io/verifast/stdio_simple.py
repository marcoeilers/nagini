from py2viper_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from py2viper_contracts.io import *
from typing import Tuple


stdout = 1 # TODO: Use TextIO as soon as #42 or #43 is fixed.


@IOOperation
def write_char_io(
        t_pre: Place,
        #fp: TextIO,
        fp: int,
        c: str,
        success: bool = Result(),
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def putchar(c: str, t1: Place) -> Tuple[bool, Place]:
    IOExists2(Place, bool)(
        lambda t2, success: (
        Requires(
            token(t1, 1) and
            write_char_io(t1, stdout, c, success, t2)
        ),
        Ensures(
            token(t2) and
            success == Result()[0] and
            t2 == Result()[1]
        )
    ))
