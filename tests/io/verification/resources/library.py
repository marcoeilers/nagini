# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from typing import Tuple


@IOOperation
def read_int_io(
        t_pre: Place,
        number: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)


def read_int(t1: Place) -> Tuple[Place, int]:
    IOExists2(Place, int)(
        lambda t2, value: (
        Requires(
            token(t1, 1) and
            read_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[0] and
            value == Result()[1]
        ),
        )
    )


@IOOperation
def write_int_io(
        t_pre: Place,
        value: int,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


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


@IOOperation
def write_string_io(
        t_pre: Place,
        value: str,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def write_string(t1: Place, value: str) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            write_string_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )
