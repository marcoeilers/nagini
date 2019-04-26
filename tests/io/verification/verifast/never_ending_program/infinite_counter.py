# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
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

from typing import Tuple

from verifast.stdio_simple import (
    putchar,
    stdout,
    write_char_io,
)


@IOOperation
def print_unary_io(
        t_pre: Place,
        number: int,
        t_end: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(number+2 if number >= 1 else 2)
    return IOExists2(Place, bool)(
        lambda t2, success: (
        (
            write_char_io(t_pre, stdout, '1', success, t2) and
            print_unary_io(t2, number - 1, t_end)
            )
        if number >= 1
        else (
            no_op_io(t_pre, t_end)
            )
    ))


@IOOperation
def infinite_counter_io(
        t_pre: Place,
        number: int) -> bool:
    return IOExists3(Place, Place, bool)(
        lambda t2, t3, success: (
        print_unary_io(t_pre, number, t2) and
        write_char_io(t2, stdout, '\n', success, t3) and
        infinite_counter_io(t3, number+1)
    ))


def main(t1: Place) -> None:
    Requires(
        token(t1, 2) and
        infinite_counter_io(t1, 0)
    )
    Ensures(
        False
    )

    count = 0
    t_cur = t1

    while True:
        Invariant(
            token(t_cur, 1) and
            infinite_counter_io(t_cur, count) and
            count >= 0
            )

        unary_count = 0

        Open(infinite_counter_io(t_cur, count))

        t1_unary = t_cur
        t_unary_end = GetGhostOutput(print_unary_io(t1_unary, count), 't_end')  # type: Place

        while (unary_count != count):
            Invariant(
                token(t1_unary, 1) and
                print_unary_io(t1_unary, count - unary_count, t_unary_end) and
                unary_count <= count
                )

            Open(print_unary_io(t1_unary, count - unary_count))

            success, t1_unary = putchar('1', t1_unary)

            unary_count += 1

        Open(print_unary_io(t1_unary, 0))

        t2 = NoOp(t1_unary)

        success, t_cur = putchar('\n', t2)

        count = count + 1
