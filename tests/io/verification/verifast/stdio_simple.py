# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import (
    MustTerminate,
)
from typing import Tuple


stdin = 0 # TODO: Use TextIO as soon as #42 or #43 is fixed.
stdout = 1 # TODO: Use TextIO as soon as #42 or #43 is fixed.
stderr = 2 # TODO: Use TextIO as soon as #42 or #43 is fixed.


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
            write_char_io(t1, stdout, c, success, t2) and
            MustTerminate(1)
        ),
        Ensures(
            token(t2) and
            success == Result()[0] and
            t2 == Result()[1]
        )
    ))


@ContractOnly
def putc(c: str, fp: int, t1: Place) -> Tuple[bool, Place]:
    IOExists2(Place, bool)(
        lambda t2, success: (
        Requires(
            token(t1, 1) and
            write_char_io(t1, fp, c, success, t2) and
            MustTerminate(1)
        ),
        Ensures(
            token(t2) and
            success == Result()[0] and
            t2 == Result()[1]
        )
    ))


@IOOperation
def read_char_io(
        t_pre: Place,
        #fp: TextIO,
        fp: int,
        c: str = Result(),
        success: bool = Result(),
        t_post: Place = Result()) -> bool:
    Terminates(False)


@ContractOnly
def getchar(t1: Place) -> Tuple[str, bool, Place]:
    IOExists3(str, bool, Place)(
        lambda c, success, t2: (
            Requires(
                token(t1, 1) and
                read_char_io(t1, stdin, c, success, t2)
            ),
            Ensures(
                c is Result()[0] and
                success == Result()[1] and
                t2 == Result()[2] and
                token(t2)
            ),
        )
    )
