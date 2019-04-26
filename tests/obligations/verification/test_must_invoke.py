# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Invariant,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from typing import Tuple, Callable


@IOOperation
def write_int_io(
        t_pre: Place,
        value: int,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


@IOOperation
def write_int_loop_io(
        t_pre: Place,
        value: int,
        ) -> bool:
    Terminates(False)
    return IOExists1(Place)(
        lambda t2: (
            write_int_io(t_pre, value, t2) and
            write_int_loop_io(t2, value)
        )
    )


@ContractOnly
def write_int(t1: Place, value: int) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            write_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )


def test1(t: Place, value: int) -> None:
    Requires(token(t, 2))
    Requires(write_int_loop_io(t, value))
    while True:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(token(t, 1) and write_int_loop_io(t, value))
        a = 2


def test2(t: Place, value: int) -> None:
    Requires(token(t, 2))
    Requires(write_int_loop_io(t, value))
    while True:
        Invariant(token(t, 1) and write_int_loop_io(t, value))
        Open(write_int_loop_io(t, value))
        t = write_int(t, value)


def test3(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                ctoken(t1) and
                write_int_io(t1, 0, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )
    return write_int(t1, 0)
