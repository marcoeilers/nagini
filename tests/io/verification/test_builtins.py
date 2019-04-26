# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Assert,
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    no_op_io,
    NoOp,
    split_io,
    Split,
    join_io,
    Join,
    set_var_io,
    SetVar,
)


@IOOperation
def test_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists6(Place, Place, Place, Place, Place, int)(
        lambda t2, t3, t4, t5, t6, res: (
        no_op_io(t_pre, t2) and
        split_io(t2, t3, t4) and
        set_var_io(t4, 1, res, t5) and
        join_io(t3, t5, t6) and
        no_op_io(t6, t_post)
    ))


def test(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t_end: (
        Requires(
            token(t1, 2) and
            test_io(t1, t_end)
        ),
        Ensures(
            token(t_end) and
            t_end == Result()
        ),
    ))

    Open(test_io(t1))

    t2 = NoOp(t1)
    t3, t4 = Split(t2)
    res, t5 = SetVar(t4, 1)
    t6 = Join(t3, t5)
    t_end = NoOp(t6)

    Assert(res == 1)

    return t_end
