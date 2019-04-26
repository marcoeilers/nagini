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
    Join,
    join_io,
    Split,
    split_io,
)
from nagini_contracts.obligations import (
    MustTerminate,
)
from verifast.stdio_simple import (
    stdout,
    stderr,
    write_char_io,
    putchar,
    putc,
)


@IOOperation
def tee_out_io(
        t_pre: Place,
        c: str,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists6(Place, Place, Place, Place, bool, bool)(
        lambda t_out1, t_err1, t_out2, t_err2, success1, success2: (
            split_io(t_pre, t_out1, t_err1) and
                write_char_io(t_out1, stdout, c, success1, t_out2) and
                write_char_io(t_err1, stderr, c, success2, t_err2) and
            join_io(t_out2, t_err2, t_post)
        )
    )


def tee_out(t1: Place, c: str) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 2) and
                tee_out_io(t1, c, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )
    Open(tee_out_io(t1, c))
    t_out1, t_err1 = Split(t1)
    success_out, t_out2 = putchar(c, t_out1)
    success_err, t_err2 = putc(c, stderr, t_err1)
    return Join(t_out2, t_err2)
