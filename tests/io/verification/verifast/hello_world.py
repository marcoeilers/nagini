from py2viper_contracts.contracts import (
    Ensures,
    Requires,
    Result,
)
from py2viper_contracts.io import *

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
            write_char_io(t2, stdout, 'i', success2, t3)
        ),
        Ensures(
            token(t3) and
            t3 == Result()
        )
    ))
    success, t2 = putchar('h', t1)
    success, t3 = putchar('i', t2)
    return t3
