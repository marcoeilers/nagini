# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import (
    MustTerminate,
)

from verifast.stdio_simple import (
    stdout,
    write_char_io,
    putchar,
)


def main(t1: Place) -> Place:
    IOExists4(Place, Place, bool, bool)(
        lambda t2, t3, success1, success2: (
        Requires(
            token(t1, 2) and
            write_char_io(t1, stdout, 'h', success1, t2) and
            write_char_io(t2, stdout, 'i', success2, t3) and
            MustTerminate(2)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        )
    ))
    success, t2 = putchar('h', t1)
    success, t3 = putchar('i', t2)
    return t3
