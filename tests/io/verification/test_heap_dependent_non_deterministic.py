# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test illustrates the problem of using heap dependent IO operations
in non-deterministic choice.
"""

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
        Ensures(Acc(self.int_field1))       # type: ignore
        Ensures(self.int_field1==value)     # type: ignore
        Ensures(Acc(self.int_field2))       # type: ignore
        Ensures(self.int_field2==value)     # type: ignore
        self.int_field1 = value
        self.int_field2 = value

    def write_int(self, b: bool, t1: Place) -> Place:
        IOExists1(Place)(
            lambda t2: (
            Requires(
                #:: ExpectedOutput(not.wellformed:insufficient.permission)|ExpectedOutput(carbon)(not.wellformed:insufficient.permission)
                token(t1, 2) and
                ((
                    Acc(self.int_field1, 1/2) and
                    write_int_io(t1, self.int_field1, t2)
                ) if b else (
                    Acc(self.int_field2, 1/2) and
                    write_int_io(t1, self.int_field2, t2)
                ))
            ),
            Ensures(
                (Acc(self.int_field1, 1/2)
                if b else
                Acc(self.int_field2, 1/2)) and
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, self.int_field1)

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
    t2 = writer.write_int(False, t1)
    return t2
