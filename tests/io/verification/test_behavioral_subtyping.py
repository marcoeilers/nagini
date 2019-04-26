# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
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

class SuperA:

    def __init__(self, t1: Place) -> None:
        self.int_field = 14

    def read_int(self, t1: Place) -> Tuple[int, Place]:
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

    def write_int1(self, t1: Place, value: int) -> Place:
        """Defining getter is not heap dependent."""
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, value, t2) and
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, value)

        return t2

    def write_int2(self, t1: Place, value: int) -> Place:
        """Defining getter is heap dependent."""
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, self.int_field, t2) and
                write_int_io(t1, value, t2)
            ),
            Ensures(
                Acc(self.int_field, 1/2) and
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, value)

        return t2


class SubA0(SuperA):
    """Exact copy of ``SuperA``."""

    def read_int(self, t1: Place) -> Tuple[int, Place]:
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

    def write_int1(self, t1: Place, value: int) -> Place:
        """Defining getter is not heap dependent."""
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, value, t2) and
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, value)

        return t2

    def write_int2(self, t1: Place, value: int) -> Place:
        """Defining getter is heap dependent."""
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, self.int_field, t2) and
                write_int_io(t1, value, t2)
            ),
            Ensures(
                Acc(self.int_field, 1/2) and
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, value)

        return t2


class SubA1(SuperA):
    """Remove heap dependent."""

    def write_int1(self, t1: Place, value: int) -> Place:
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                write_int_io(t1, value, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, value)

        return t2

    def write_int2(self, t1: Place, value: int) -> Place:
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                write_int_io(t1, value, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, value)

        return t2


class SubA2(SuperA):
    """Remove heap non-dependent."""

    def write_int1(self, t1: Place, value: int) -> Place:
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                # Getter is heap dependent, therefore need access to
                # self.int_field.
                Acc(self.int_field, 1/2) and
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, self.int_field)

        return t2

    def write_int2(self, t1: Place, value: int) -> Place:
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


class SubA3(SuperA):
    """Remove heap non-dependent."""

    # Defining getter is changed from heap non-dependent to heap
    # dependent. Overriding method takes less permission than
    # overriden method (and SubA2.write_int1). As a result, equality is
    # havoced and verifier manages to verify the method.
    def write_int1(self, t1: Place, value: int) -> Place:
        IOExists1(Place)(
            lambda t2: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/4) and # Ask less permission.
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                # Getter is heap dependent, therefore need access to
                # self.int_field.
                Acc(self.int_field, 1/4) and  # Ask less permission.
                token(t2) and
                t2 == Result()
            ),
            )
        )

        t2 = write_int(t1, self.int_field)

        return t2


class SubA4(SuperA):
    """Copy of ``SuperA`` just with different variable names."""

    def read_int(self, t1: Place) -> Tuple[int, Place]:
        IOExists2(Place, int)(
            lambda t2_new, value_new: (
            Requires(
                token(t1, 2) and
                read_int_io(t1, value_new, t2_new)
            ),
            Ensures(
                token(t2_new) and
                t2_new == Result()[1] and
                value_new == Result()[0]
            ),
            )
        )

        t2_new, number_new = read_int(t1)

        return number_new, t2_new

    def write_int1(self, t1: Place, value: int) -> Place:
        """Defining getter is not heap dependent."""
        IOExists1(Place)(
            lambda t2_new: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, value, t2_new) and
                write_int_io(t1, self.int_field, t2_new)
            ),
            Ensures(
                token(t2_new) and
                t2_new == Result()
            ),
            )
        )

        t2_new = write_int(t1, value)

        return t2_new

    def write_int2(self, t1: Place, value: int) -> Place:
        """Defining getter is heap dependent."""
        IOExists1(Place)(
            lambda t2_new: (
            Requires(
                token(t1, 2) and
                Acc(self.int_field, 1/2) and
                write_int_io(t1, self.int_field, t2_new) and
                write_int_io(t1, value, t2_new)
            ),
            Ensures(
                Acc(self.int_field, 1/2) and
                token(t2_new) and
                t2_new == Result()
            ),
            )
        )

        t2_new = write_int(t1, value)

        return t2_new
