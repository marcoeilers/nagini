# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Pure,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from typing import Tuple


@IOOperation
def read_something_io(
        t_pre: Place,
        result1: int = Result(),
        result2: bool = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


@ContractOnly
def read_something(t1: Place) -> Tuple[Place, int, bool]:
    IOExists3(Place, int, bool)(
        lambda t2, value1, value2: (
        Requires(
            token(t1, 1) and
            read_something_io(t1, value1, value2, t2)
        ),
        Ensures(
            token(t2) and
            Result()[0] == t2 and
            Result()[1] == value1 and
            Result()[2] == value2
        ),
        )
    )


@IOOperation
def write_something_io(
        t_pre: Place,
        arg1: int,
        arg2: bool,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


@ContractOnly
def write_something(t1: Place, value1: int, value2: bool) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            write_something_io(t1, value1, value2, t2)
        ),
        Ensures(
            token(t2) and
            Result() == t2
        ),
        )
    )
