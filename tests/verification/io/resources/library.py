from py2viper_contracts.contracts import (
    Requires,
    Predicate,
    Result,
    Assert,
)
from py2viper_contracts.io import *
from typing import Tuple, Callable


@IOOperation
def read_int_io(
        t_pre: Place,
        number: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)


def read_int(t1: Place) -> Tuple[Place, int]:
    IOExists = lambda t2, value: (
        Requires(
            token(t1) and
            read_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[0] and
            value == Result()[1]
        )
    )   # type: Callable[[Place, int], Tuple[bool, bool]]


@IOOperation
def write_int_io(
        t_pre: Place,
        value: int,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def write_int(t1: Place, value: int) -> Place:
    IOExists = lambda t2: (
        Requires(
            token(t1) and
            write_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        )
    )   # type: Callable[[Place], Tuple[bool, bool]]


@IOOperation
def write_string_io(
        t_pre: Place,
        value: str,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def write_string(t1: Place, value: str) -> Place:
    IOExists = lambda t2: (
        Requires(
            token(t1) and
            write_string_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        )
    )   # type: Callable[[Place], Tuple[bool, bool]]
