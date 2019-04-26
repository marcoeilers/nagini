# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Ensures, Result
from nagini_contracts.io_contracts import *
from typing import Tuple, Callable

from resources.library import write_string_io, write_string


def hello(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 2) and
            write_string_io(t1, "Hello World!", t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        )
        )
    )

    t2 = write_string(t1, "Hello World!")

    return t2


def hello2(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 2) and
            write_string_io(t1, "Hello World!", t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        )
        )
    )

    #:: ExpectedOutput(call.precondition:insufficient.permission)
    t2 = write_string(t1, "Hello World")

    return t2


def hello3(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            write_string_io(t1, "Hello World!", t2)
        ),
        Ensures(
            #:: ExpectedOutput(postcondition.violated:insufficient.permission)
            token(t2) and
            t2 == Result()
        ),
        )
    )

    return t1
