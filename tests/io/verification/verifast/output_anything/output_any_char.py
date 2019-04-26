# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
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


@IOOperation
def set_var_io(
        t_pre: Place,
        c: str = Result(),
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def SetVar(t1: Place, value: str) -> Place:
    """A ghost helper procedure for creating unspecified values."""
    IOExists2(str, Place)(
        lambda c, t2: (
            Requires(
                token(t1, 1) and
                set_var_io(t1, c, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result() and
                c is value
            ),
        )
    )


@IOOperation
def output_anything(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists3(str, Place, bool)(
        lambda c, t2, success: (
            set_var_io(t_pre, c, t2) and
            write_char_io(t2, stdout, c, success, t_post)
        )
    )


def get_any_char() -> str:
    """Return some unknown character."""
    Requires(MustTerminate(1))
    return "c"


def main(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 2) and
                output_anything(t1, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2)
            ),
        )
    )
    i = get_any_char()

    Open(output_anything(t1))
    t2 = SetVar(t1, i)
    success, t3 = putchar(i, t2)
    return t3
