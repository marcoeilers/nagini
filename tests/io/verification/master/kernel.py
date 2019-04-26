# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Pure,
    Result,
    Requires,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    gap_io,
    Gap,
    end_io,
    End,
)
from nagini_contracts.obligations import (
    MustTerminate,
)
from typing import Tuple


class File:
    pass


@IOOperation
def open_io(
        t_pre: Place,
        file_name: str,
        result: File = Result(),
        t_post: Place = Result()) -> bool:
  Terminates(True)


@ContractOnly
def open(t1: Place, file_name: str) -> Tuple[File, Place]:
    IOExists2(Place, File)(
        lambda t2, fp: (
            Requires(
                token(t1, 1) and
                open_io(t1, file_name, fp, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()[1] and
                fp is Result()[0]
            ),
        )
    )


@IOOperation
def write_io(
        t_pre: Place,
        fp: File,
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def write(t1: Place, fp: File) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 1) and
                write_io(t1, fp, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )


@IOOperation
def close_io(
        t_pre: Place,
        fp: File,
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def close(t1: Place, fp: File) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 1) and
                close_io(t1, fp, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )


@IOOperation
def send_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def send(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 1) and
                send_io(t1, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )


@IOOperation
def notify_io(
        t_pre: Place) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists1(Place)(
        lambda t2: (
            send_io(t_pre, t2) and
            end_io(t2)
        )
    )


@IOOperation
def resource_io(
        t_pre: Place,
        file_name: str,
        t_post: Place = Result()) -> bool:
    return IOExists5(Place, Place, Place, Place, File)(
        lambda t2, t3, t4, t5, fp: (
            open_io(t_pre, file_name, fp, t2) and
            gap_io(t2, t3) and
            write_io(t3, fp, t4) and
            gap_io(t4, t5) and
            close_io(t5, fp, t_post)
        )
    )


def potentialy_non_terminating() -> None:
    pass


def notify(t1: Place) -> None:
    Requires(
        token(t1, 2) and
        notify_io(t1) and
        MustTerminate(2)
    )

    Open(notify_io(t1))

    t2 = send(t1);

    t3 = End(t2)


def run(t_pre1: Place, t_pre2: Place, file_name: str) -> Place:
    IOExists1(Place)(
        lambda t_post: (
            Requires(
                token(t_pre1, 3) and
                resource_io(t_pre1, file_name, t_post) and
                ctoken(t_pre2) and
                notify_io(t_pre2)
            ),
            Ensures(
                token(t_post) and
                t_post == Result()
            ),
        )
    )

    Open(resource_io(t_pre1, file_name))

    fp, t2 = open(t_pre1, file_name)

    t3 = Gap(t2)

    potentialy_non_terminating()

    notify(t_pre2)

    t4 = write(t3, fp)

    t5 = Gap(t4)

    potentialy_non_terminating()

    t_post = close(t5, fp)

    return t_post
