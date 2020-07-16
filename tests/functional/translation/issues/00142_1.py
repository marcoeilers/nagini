# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from typing import Tuple, Callable


@IOOperation
def write_string_io(
        t_pre: Place,
        value: str,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


@ContractOnly
def write_string(t1: Place, value: str) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            write_string_io(t1, value, t2)
        ),
        Ensures(
            #:: ExpectedOutput(invalid.program:invalid.contract.position)
            not(token(t2))
        ),
        )
    )


def hello(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 2) and
            write_string_io(t1, "Hello World!", t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        )
        )
    )

    t2 = write_string(t1, "Hello World!")

    return t2
