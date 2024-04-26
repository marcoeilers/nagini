# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Ensures,
    Requires,
    Result,
    Implies
)
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import Tuple, Union

from resources.library import (
    read_int_io,
    read_int,
    write_int_io,
    write_int,
)


# Read only.


@IOOperation
def write_two_ints_io(
        t_pre: Place,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
    return IOForall(int,
        lambda value: IOExists(Place)(
            lambda t2: (
                write_int_io(t_pre, value, t2) and
                write_int_io(t2, value * 2, t_post)
        )
    ))


def write_four_ints_1(t1: Place) -> Place:
    IOExists2(Place, Place)(
        lambda t2, t3: (
        Requires(
            token(t1, 2) and
            write_two_ints_io(t1, t2) and
            write_two_ints_io(t2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    Open(write_two_ints_io(t1))

    t2 = write_int(t1, 4)
    t3 = write_int(t2, 8)

    Open(write_two_ints_io(t3))

    t4 = write_int(t3, 3)
    t5 = write_int(t4, 6)

    return t5


def write_four_ints_2(t1: Place) -> Place:
    IOExists2(Place, Place)(
        lambda t2, t3: (
        Requires(
            token(t1, 2) and
            write_two_ints_io(t1, t2) and
            write_two_ints_io(t2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        ),
        )
    )

    # See comment below.
    marco = (t1, True)
    wow(marco)
    wow2(marco)

    Open(write_two_ints_io(t1))

    t2 = write_int(t1, 4)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    t3 = write_int(t2, 9)

    #:: ExpectedOutput(carbon)(exhale.failed:insufficient.permission)
    Open(write_two_ints_io(t3))

    t4 = write_int(t3, 3)
    t5 = write_int(t4, 6)

    return t5


def write_four_ints_3(t1: Place) -> Place:
    IOExists2(Place, Place)(
        lambda t2, t3: (
        Requires(
            token(t1, 2) and
            write_two_ints_io(t1, t2) and
            write_two_ints_io(t2, t3)
        ),
        Ensures(
            #:: ExpectedOutput(postcondition.violated:insufficient.permission)
            token(t3) and
            t3 == Result()
        ),
        )
    )

    Open(write_two_ints_io(t1))

    t2 = write_int(t1, 4)
    t3 = write_int(t2, 8)

    return t3


def write_four_ints_4(t1: Place) -> Place:
    IOExists2(Place, Place)(
        lambda t2, t3: (
        Requires(
            token(t1, 2) and
            write_two_ints_io(t1, t2) and
            write_two_ints_io(t2, t3)
        ),
        Ensures(
            #:: ExpectedOutput(carbon)(postcondition.violated:insufficient.permission)
            token(t3) and
            t3 == Result()
        ),
        )
    )

    Open(write_two_ints_io(t1))

    t2 = write_int(t1, 4)
    t3 = write_int(t2, 8)

    Open(write_two_ints_io(t3))

    t4 = write_int(t3, 3)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    t5 = write_int(t4, 3)

    return t5


# ME: This test at some point had missing errors in Carbon after changing tuple-related axioms that I cannot reproduce
# any more.
# Here I'm adding some calls that should trigger any dangerous cases I can think of related to those changes, hoping
# that if there is actually a problem, it will be triggered again in the future.

def wow(t: Tuple[Place, int]) -> None:
    Requires(MustTerminate(1))
    Requires(bool(t[1]))
    Ensures(Implies(isinstance(t[1], bool), t[1] is True))
    Ensures(t == (t[0], t[1]))
    Ensures(Implies(isinstance(t[1], bool), t == (t[0], True)))
    Ensures((t, t, 3) == (t, t, 1 + 2))
    pass


def wow2(t: Tuple[object, bool]) -> Union[int, Tuple[object, object]]:
    Requires(MustTerminate(1))
    Ensures(Result() is t)
    Ensures(Result() == t)
    Ensures(isinstance(Result(), object))
    Ensures(isinstance(t[1], int))
    return t
