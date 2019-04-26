# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from typing import Tuple

from resources.library import (
    read_int_io,
    read_int,
    write_int_io,
    write_int,
)


# Read only.


@IOOperation
def read_int_twice_io(
        t_pre: Place,
        number1: int = Result(),
        number2: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
    return IOExists1(Place)(
        lambda t2: (
        read_int_io(t_pre, number1, t2) and
        read_int_io(t2, number2, t_post)
        )
    )


@IOOperation
def write_int_twice_io(
        t_pre: Place,
        number1: int,
        number2: int,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists1(Place)(
        lambda t2: (
        write_int_io(t_pre, number1, t2) and
        write_int_io(t2, number2, t_post)
        )
    )


def read_int_twice1(t1: Place) -> Tuple[Place, int, int]:
    IOExists3(Place, int, int)(
        lambda t2, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[0] and
            value1 == Result()[1] and
            value2 == Result()[2]
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    return t3, number1, number2


def read_int_twice2(t1: Place) -> Tuple[Place, int, int]:
    IOExists3(Place, int, int)(
        lambda t2, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2)
        ),
        Ensures(
            #:: ExpectedOutput(postcondition.violated:assertion.false)
            token(t2) and
            t2 == Result()[0] and
            value1 == Result()[1] and
            value2 == Result()[2]
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    return t3, number2, number1


def read_int_twice3(t1: Place) -> Tuple[Place, int, int]:
    IOExists3(Place, int, int)(
        lambda t2, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[0] and
            value1 == Result()[1] and
            value2 == Result()[2]
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, number2 = read_int(t1)
    t3, number1 = read_int(t2)

    return t3, number2, number1


def read_int_twice4(t1: Place) -> Tuple[Place, int, int]:
    IOExists3(Place, int, int)(
        lambda t2, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[0] and
            value1 == Result()[1] and
            value2 == Result()[2]
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, value1 = read_int(t1)
    t3, value2 = read_int(t2)

    return t3, value1, value2


# Read and write.


def read_write_int_twice1(t1: Place) -> Place:
    IOExists4(Place, Place, int, int)(
        lambda t2, t3, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2) and
            write_int_twice_io(t2, value1, value2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    Open(write_int_twice_io(t3, number1, number2))

    t4 = write_int(t3, number1)
    t5 = write_int(t4, number2)

    return t5


def read_write_int_twice2(t1: Place) -> Place:
    IOExists4(Place, Place, int, int)(
        lambda t2, t3, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2) and
            write_int_twice_io(t2, value1, value2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    #:: ExpectedOutput(exhale.failed:insufficient.permission)
    Open(write_int_twice_io(t3, number2, number1))

    t4 = write_int(t3, number1)
    t5 = write_int(t4, number2)

    return t5


def read_write_int_twice3(t1: Place) -> Place:
    IOExists4(Place, Place, int, int)(
        lambda t2, t3, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2) and
            write_int_twice_io(t2, value1, value2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    #:: ExpectedOutput(call.precondition:insufficient.permission)
    t4 = write_int(t3, number1)
    t5 = write_int(t4, number2)

    return t5


def read_write_int_twice4(t1: Place) -> Place:
    IOExists4(Place, Place, int, int)(
        lambda t2, t3, value1, value2: (
        Requires(
            token(t1, 2) and
            read_int_twice_io(t1, value1, value2, t2) and
            write_int_twice_io(t2, value1, value2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    Open(read_int_twice_io(t1))

    t2, number1 = read_int(t1)
    t3, number2 = read_int(t2)

    Open(write_int_twice_io(t3, number1, number2))

    #:: ExpectedOutput(call.precondition:insufficient.permission)
    t4 = write_int(t3, number2)
    #:: ExpectedOutput(carbon)(call.precondition:insufficient.permission)
    t5 = write_int(t4, number1)

    return t5
