from py2viper_contracts.contracts import (
    Import,
    Requires,
    Ensures,
    Invariant,
)
from py2viper_contracts.io import *
from verifast.stdio_simple import (
    putchar,
    stdout,
    write_char_io,
)
Import('../stdio_simple.py')


@IOOperation
def yes_io(t_pre: Place) -> bool:
    Terminates(False)
    return IOExists4(Place, Place, bool, bool)(
        lambda t2, t3, success1, success2: (
        write_char_io(t_pre, stdout, 'y', success1, t2) and
        write_char_io(t2, stdout, '\n', success2, t3) and
        yes_io(t3)
    ))


def main(t1: Place) -> None:
    Requires(
        token(t1) and
        yes_io(t1)
    )
    Ensures(
        False
    )

    t = t1

    while True:
        Invariant(
            token(t) and
            yes_io(t)
            )

        Open(yes_io(t))
        success, t2 = putchar('y', t)
        success, t = putchar('\n', t2)
