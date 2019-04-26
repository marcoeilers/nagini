# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Ensures, Result
from nagini_contracts.io_contracts import *
from typing import Tuple, Callable

from resources.library import (
    read_int_io,
    read_int,
    write_int_io,
    write_int,
    write_string_io,
    write_string,
)


def write_implementation_defined1(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 2) and
            write_string_io(t1, "Hello!", t2) and
            write_string_io(t1, "Hallo!", t2) and
            write_string_io(t1, "Sveikas!", t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )

    t2 = write_string(t1, "Hello!")
    return t2


def write_implementation_defined2(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 2) and
            write_string_io(t1, "Hello!", t2) and
            write_string_io(t1, "Hallo!", t2) and
            write_string_io(t1, "Sveikas!", t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )

    t2 = write_string(t1, "Hallo!")
    return t2


def write_implementation_defined3(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 2) and
            write_string_io(t1, "Hello!", t2) and
            write_string_io(t1, "Hallo!", t2) and
            write_string_io(t1, "Sveikas!", t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )

    t2 = write_string(t1, "Sveikas!")
    return t2


def write_non_negative(t1: Place) -> Place:
    IOExists3(Place, Place, int)(
        lambda t2, t3, value: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value, t2) and
            (
                write_int_io(t2, value, t3)
                if value >= 0
                else write_int_io(t2, -value, t3)
                )

        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    t2, number = read_int(t1)

    if number >= 0:
        t3 = write_int(t2, number)
    else:
        t3 = write_int(t2, -number)

    return t3


def write_only_positive(t1: Place) -> Place:
    IOExists3(Place, Place, int)(
        lambda t2, t3, value: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value, t2) and
            write_int_io(t2, value, t3)
        ),
        Ensures(
            (token(t3) and t3 == Result())
            if value > 0
            else (
                token(t2) and
                write_int_io(t2, value, t3) and
                t2 == Result()
            )
        ),
        )
    )

    t2, number = read_int(t1)

    if number > 0:
        t3 = write_int(t2, number)
    else:
        t3 = t2

    return t3
