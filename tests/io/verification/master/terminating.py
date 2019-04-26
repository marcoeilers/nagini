# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Implies,
    Invariant,
    Pure,
    Result,
    Requires,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import (
    MustTerminate,
)


@IOOperation
def print_int_io(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def print_int(t1: Place, value: int) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 1) and
                print_int_io(t1, value, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                Result() == t2
            ),
        )
    )


@Pure
def max(a: int, b: int) -> int:
    return a if a > b else b


@IOOperation
def print_sequence_io(
        t_pre: Place,
        n: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(n + 1, 2))
    return IOExists1(Place)(
        lambda t2: (
            (
                print_int_io(t_pre, n, t2) and
                print_sequence_io(t2, n-1, t_post)
                )
            if n > 1
            else print_int_io(t_pre, 1, t_post)
        )
    )


def print_sequence1(t1: Place, n: int) -> Place:
    """Prints n(n-1)...1."""
    IOExists1(Place)(
        lambda t2: (
            Requires(
                n > 0 and
                token(t1, n+1) and
                print_sequence_io(t1, n, t2) and
                MustTerminate(n+1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )

    Open(print_sequence_io(t1, n))

    t3 = print_int(t1, n)

    if n > 1:
        t2 = print_sequence1(t3, n-1)
    else:
        t2 = t3

    return t2


def print_sequence2(t1: Place, n: int) -> Place:
    """Prints n(n-1)...1."""
    IOExists1(Place)(
        lambda t2: (
            Requires(
                n > 0 and
                token(t1, 2) and
                print_sequence_io(t1, n, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )

    t = t1

    t2 = GetGhostOutput(print_sequence_io(t, n), 't_post')  # type: Place

    while n > 1:
        Invariant(
            token(t, 1) and
            print_sequence_io(t, n, t2) and
            MustTerminate(n)
        )
        Open(print_sequence_io(t, n))
        t = print_int(t, n)
        n -= 1

    Open(print_sequence_io(t, n))
    t = print_int(t, 1)
    return t


def print_sequence3(t1: Place, n: int) -> Place:
    """Prints n(n-1)...1."""
    IOExists1(Place)(
        lambda t2: (
            Requires(
                n > 0 and
                token(t1, 2) and
                print_sequence_io(t1, n, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )

    t = t1
    Open(print_sequence_io(t, n))
    t2 = GetGhostOutput(print_sequence_io(t, n), 't_post')  # type: Place

    while n > 1:
        IOExists1(Place)(
            lambda t_next: (
                Invariant(
                    token(t, 1) and
                    Implies(n > 1,
                        print_int_io(t, n, t_next) and
                        print_sequence_io(t_next, n-1, t2)) and
                    Implies(not n > 1,
                        print_int_io(t, n, t2))
                ),
                Invariant(
                    MustTerminate(n)
                ),
            )
        )
        t = print_int(t, n)
        n -= 1
        Open(print_sequence_io(t, n))

    t = print_int(t, n)
    return t


def print_sequence4(t1: Place, n: int) -> Place:
    """Prints n(n-1)...1."""
    IOExists1(Place)(
        lambda t2: (
            Requires(
                n > 0 and
                token(t1, 2) and
                print_sequence_io(t1, n, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )

    t = t1
    Open(print_sequence_io(t, n))
    t2 = GetGhostOutput(print_sequence_io(t, n), 't_post')  # type: Place

    while n > 1:
        IOExists1(Place)(
            lambda t_next: (
                Invariant(
                    token(t, 1) and
                    Implies(n > 1,
                        print_int_io(t, n, t_next) and
                        print_sequence_io(t_next, n-1, t2)) and
                    Implies(not n > 1,
                        print_int_io(t, n, t2)) and
                    MustTerminate(n)
                )
            )
        )
        t = print_int(t, n)
        n -= 1
        Open(print_sequence_io(t, n))

    t = print_int(t, n)
    return t
