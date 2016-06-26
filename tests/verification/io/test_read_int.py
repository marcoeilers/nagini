from py2viper_contracts.contracts import Requires, Ensures, Result, Import
from py2viper_contracts.io import *
from typing import Tuple, Callable

from resources.library import (
    read_int_io,
    read_int,
    write_int_io,
    write_int,
)
Import('resources/library.py')


# Read only.


def read_int1(t1: Place) -> Tuple[int, Place]:
    IOExists = lambda t2, value: (
        Requires(
            token(t1) and
            read_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[1] and
            value == Result()[0]
        )
    )   # type: Callable[[Place, int], Tuple[bool, bool]]

    t2, number = read_int(t1)

    return number, t2


def read_int2(t1: Place) -> Tuple[int, int, Place]:
    IOExists = lambda t3, t2, value1, value2: (
        Requires(
            token(t1) and
            read_int_io(t1, value1, t2) and
            read_int_io(t2, value2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()[2] and
            value1 == Result()[0] and
            value2 == Result()[1]
        )
    )   # type: Callable[[Place, Place, int, int], Tuple[bool, bool]]

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    return number1, number2, t3


def read_int3(t1: Place) -> Tuple[int, int, Place]:
    IOExists = lambda t3, t2, value1, value2: (
        Requires(
            token(t1) and
            read_int_io(t1, value1, t2) and
            read_int_io(t2, value2, t3)
        ),
        Ensures(
            #:: ExpectedOutput(postcondition.violated:assertion.false)
            token(t3) and
            t3 == Result()[2] and
            value1 == Result()[0] and
            value2 == Result()[1]
        )
    )   # type: Callable[[Place, Place, int, int], Tuple[bool, bool]]

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    return number2, number1, t3


# Read and write.


def read_write_int1(t1: Place) -> Place:
    IOExists = lambda t2, t3, value: (
        Requires(
            token(t1) and
            read_int_io(t1, value, t2) and
            write_int_io(t2, value, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        )
    )   # type: Callable[[Place, Place, int], Tuple[bool, bool]]

    t2, number = read_int(t1)
    t3 = write_int(t2, number)

    return t3


def read_write_int2(t1: Place) -> Place:
    IOExists = lambda t2, t3, t4, t5, value1, value2: (
        Requires(
            token(t1) and
            read_int_io(t1, value1, t2) and
            read_int_io(t2, value2, t3) and
            write_int_io(t3, value1, t4) and
            write_int_io(t4, value2, t5)
        ),
        Ensures(
            token(t5) and
            t5 == Result()
        )
    )   # type: Callable[[Place, Place, Place, Place, int, int], Tuple[bool, bool]]

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)
    t4 = write_int(t3, number1)
    t5 = write_int(t4, number2)

    return t5


# TODO: Should be uncommented as soon as MissingOutput directive is supported.
#   def read_write_int3(t1: Place) -> Place:
#       IOExists = lambda t2, t3, t4, t5, value1, value2: (
#           Requires(
#               token(t1) and
#               read_int_io(t1, value1, t2) and
#               read_int_io(t2, value2, t3) and
#               write_int_io(t3, value1, t4) and
#               write_int_io(t4, value2, t5)
#           ),
#           Ensures(
#               token(t5) and
#               t5 == Result()
#           )
#       )   # type: Callable[[Place, Place, Place, Place, int, int], Tuple[bool, bool]]

#       t2, number1 = read_int(t1)
#       t3, number2 = read_int(t2)
#       #:: ExpectedOutput(call.precondition:insufficient.permission)
#       t4 = write_int(t3, number2)
#       #:: ExpectedOutput(call.precondition:insufficient.permission)
#       #:: MissingOutput(call.precondition:insufficient.permission, /silicon/issue/34/)
#       t5 = write_int(t4, number1)

#       return t5
