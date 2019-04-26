# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    Requires,
    Ensures,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import Tuple

from resources.library import (
    write_int_io,
    write_int,
)


class WriterSuper:

    def __init__(self, value: int) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.int_field) and self.int_field==value) # type: ignore
        self.int_field = value

    def write_int(self, t1: Place) -> Place:
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                Acc(self.int_field, 1/2) and
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, self.int_field)

        return t2


def client1(t1: Place, value: int) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 3) and
            write_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )

    writer = WriterSuper(value)
    t2 = writer.write_int(t1)
    return t2


class WriterSub(WriterSuper):

    # Note: the method is identical to the one in WriterSuper.
    def write_int(self, t1: Place) -> Place:
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                Acc(self.int_field, 1/2) and
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, self.int_field)

        return t2


def client2(t1: Place, value: int) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 3) and
            write_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )

    writer = WriterSub(value)
    t2 = writer.write_int(t1)
    return t2
