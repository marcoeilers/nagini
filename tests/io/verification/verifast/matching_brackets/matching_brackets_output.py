# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    no_op_io,
    NoOp,
)
from nagini_contracts.obligations import (
    MustTerminate,
)
from verifast.stdio_simple import (
    stdout,
    write_char_io,
    putchar,
)


@IOOperation
def matching_brackets_helper(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    return IOExists5(bool, bool, Place, Place, Place)(
        lambda success1, success2, t_open, t_center, t_close: (
            write_char_io(t_pre, stdout, '(', success1, t_open) and
            matching_brackets(t_open, t_center) and
            write_char_io(t_center, stdout, ')', success2, t_close) and
            matching_brackets(t_close, t_post)
        )
    )


@IOOperation
def matching_brackets(
        t1: Place,
        t2: Place = Result()) -> bool:
    return no_op_io(t1, t2) and matching_brackets_helper(t1, t2)


def main(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 2) and
                matching_brackets(t1, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2)
            ),
        )
    )
    Open(matching_brackets(t1))
    Open(matching_brackets_helper(t1))
    success, t2 = putchar('(', t1)
    Open(matching_brackets(t2))
    t3 = NoOp(t2)
    success, t4 = putchar(')', t3)
    Open(matching_brackets(t4))
    t5 = NoOp(t4)
    return t5
