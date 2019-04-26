# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    ContractOnly,
    Requires,
    Ensures,
    Predicate,
    Result,
    Unfold,
    Fold,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    no_op_io,
    NoOp,
)
from nagini_contracts.obligations import (
    MustTerminate,
)
from typing import Tuple, Optional


# SYSCALL


@IOOperation
def syscall_putchar_io(
        t_pre: Place,
        c: str,
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def syscall_putchar(t1: Place, c: str) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            syscall_putchar_io(t1, c, t2) and
            MustTerminate(1)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
    ))

# STDLIB

class StandardLibrary:

    def __init__(self) -> None:
        self.buffer = None      # type: str
        self.buffer_size = 0


@Predicate
def stdlib(lib: StandardLibrary, t1: Place, t2: Place) -> bool:
    return (
        Acc(lib.buffer) and
        Acc(lib.buffer_size) and
        (
            syscall_putchar_io(t1, lib.buffer, t2)
            if lib.buffer_size == 1
            else (
                lib.buffer_size == 0 and
                t1 == t2
            )
        )
    )


@IOOperation
def stdlib_putchar_io(
        t_pre: Place,
        c: str,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return syscall_putchar_io(t_pre, c, t_post)


def stdlib_putchar(
        lib: StandardLibrary,
        c: str,
        t1: Place,
        t_postponed: Place) -> Tuple[Place, Place]:
    IOExists2(Place, Place)(
        lambda t1_new, t2: (
            Requires(
                token(t1, 2) and
                stdlib(lib, t1, t_postponed) and
                stdlib_putchar_io(t_postponed, c, t2) and
                MustTerminate(2)
            ),
            Ensures(
                t1_new == Result()[0] and
                t2 == Result()[1] and
                stdlib(lib, t1_new, t2) and
                token(t1_new, 2)
            ),
        )
    )
    Unfold(stdlib(lib, t1, t_postponed))
    Open(stdlib_putchar_io(t_postponed, c))
    if lib.buffer_size == 1:
        t2 = syscall_putchar(t1, lib.buffer)
        t3 = syscall_putchar(t2, c)
        lib.buffer_size = 0
        Fold(stdlib(lib, t3, t3))
        return t3, t3
    else:
        lib.buffer = c
        lib.buffer_size = 1
        t4 = GetGhostOutput(stdlib_putchar_io(t_postponed, c), 't_post') # type: Place
        Fold(stdlib(lib, t1, t4))
        return t1, t4


def stdlib_flush_stdout(
        lib: StandardLibrary,
        t1: Place,
        t_postponed: Place) -> None:
    Requires(
        token(t1, 3) and
        stdlib(lib, t1, t_postponed) and
        MustTerminate(2)
    )
    Ensures(
        token(t_postponed, 3) and
        stdlib(lib, t_postponed, t_postponed)
    )
    Unfold(stdlib(lib, t1, t_postponed))
    if lib.buffer_size == 1:
        syscall_putchar(t1, lib.buffer)
        lib.buffer_size = 0
    Fold(stdlib(lib, t_postponed, t_postponed))


# USER


def main(t1: Place, lib: StandardLibrary) -> Place:
    IOExists2(Place, Place)(
        lambda t2, t3: (
            Requires(
                token(t1) and
                stdlib(lib, t1, t1) and
                stdlib_putchar_io(t1, 'h', t2) and
                stdlib_putchar_io(t2, 'i', t3) and
                MustTerminate(4)
            ),
            Ensures(
                token(t3, 10) and
                stdlib(lib, t3, t3) and
                t3 == Result()
            ),
        )
    )
    t2, t_postponed = stdlib_putchar(lib, 'h', t1, t1)
    t3, t_postponed = stdlib_putchar(lib, 'i', t2, t_postponed)
    stdlib_flush_stdout(lib, t3, t_postponed)
    return t_postponed
