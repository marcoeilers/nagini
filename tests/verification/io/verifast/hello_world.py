from py2viper_contracts.contracts import (
    ContractOnly,
    Requires,
    Ensures,
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
            token(t1) and
            write_char_io(t1, stdout, c, success, t2)
        ),
        Ensures(
            token(t2) and
            success == Result()[0] and
            t2 == Result()[1]
        )
    ))



def main(t1: Place) -> Place:
    IOExists4(Place, Place, bool, bool)(
        lambda t2, t3, success1, success2: (
        Requires(
            token(t1) and
            write_char_io(t1, stdout, 'h', success1, t2) and
            write_char_io(t2, stdout, 'i', success2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        )
    ))
    success, t2 = putchar('h', t1)
    success, t3 = putchar('i', t2)
    return t3
