# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Invariant,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    no_op_io,
    NoOp,
)
from verifast.stdio_simple import (
    stdin,
    read_char_io,
    getchar,
)
from verifast.tee.tee_out import (
    tee_out_io,
    tee_out,
)


@IOOperation
def tee_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    return IOExists4(str, bool, Place, Place)(
        lambda c, success, t_read, t_out: (
            read_char_io(t_pre, stdin, c, success, t_read) and
            (
                (
                tee_out_io(t_read, c, t_out) and
                tee_io(t_out, t_post)
                )
                if success
                else (
                    no_op_io(t_read, t_post)
                )
            )
        )
    )


@IOOperation
def main_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    return tee_io(t_pre, t_post)


def main(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1) and
                main_io(t1, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )
    t2 = GetGhostOutput(main_io(t1), 't_post')  # type: Place
    Open(main_io(t1))
    success = True
    t_loop = t1
    while success:
        Invariant(
            token(t_loop, 1) and tee_io(t_loop, t2)
            if success
            else token(t_loop) and no_op_io(t_loop, t2)
        )
        Open(tee_io(t_loop))
        c, success, t_loop = getchar(t_loop)
        if success:
            t_loop = tee_out(t_loop, c)
    return NoOp(t_loop)
