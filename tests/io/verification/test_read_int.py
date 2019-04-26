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
)


# Read only.


def read_int1(t1: Place) -> Tuple[int, Place]:
    IOExists2(Place, int)(
        lambda t2, value: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[1] and
            value == Result()[0]
        ),
        )
    )

    t2, number = read_int(t1)

    return number, t2


def read_int2(t1: Place) -> Tuple[int, int, Place]:
    IOExists4(Place, Place, int, int)(
        lambda t3, t2, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value1, t2) and
            read_int_io(t2, value2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()[2] and
            value1 == Result()[0] and
            value2 == Result()[1]
        ),
        )
    )

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    return number1, number2, t3


def read_int3(t1: Place) -> Tuple[int, int, Place]:
    IOExists4(Place, Place, int, int)(
        lambda t3, t2, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value1, t2) and
            read_int_io(t2, value2, t3)
        ),
        Ensures(
            #:: ExpectedOutput(postcondition.violated:assertion.false)
            token(t3) and
            t3 == Result()[2] and
            value1 == Result()[0] and
            value2 == Result()[1]
        ),
        )
    )

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    return number2, number1, t3


# Read and write.


def read_write_int1(t1: Place) -> Place:
    IOExists3(Place, Place, int)(
        lambda t2, t3, value: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value, t2) and
            write_int_io(t2, value, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    t2, number = read_int(t1)
    t3 = write_int(t2, number)

    return t3


def read_write_int2(t1: Place) -> Place:
    IOExists6(Place, Place, Place, Place, int, int)(
        lambda t2, t3, t4, t5, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value1, t2) and
            read_int_io(t2, value2, t3) and
            write_int_io(t3, value1, t4) and
            write_int_io(t4, value2, t5)
        ),
        Ensures(
            token(t5) and
            t5 == Result()
        ),
        )
    )

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)
    t4 = write_int(t3, number1)
    t5 = write_int(t4, number2)

    return t5


def read_write_int3(t1: Place) -> Place:
    IOExists6(Place, Place, Place, Place, int, int)(
        lambda t2, t3, t4, t5, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_io(t1, value1, t2) and
            read_int_io(t2, value2, t3) and
            write_int_io(t3, value1, t4) and
            write_int_io(t4, value2, t5)
        ),
        Ensures(
            token(t5) and
            t5 == Result()
        ),
        )
    )

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    t4 = write_int(t3, number2)
    #:: ExpectedOutput(carbon)(call.precondition:insufficient.permission)
    t5 = write_int(t4, number1)

    return t5
