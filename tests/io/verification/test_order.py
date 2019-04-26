# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Tests if IO operation can be used before its definition.
"""


from nagini_contracts.contracts import (
    ContractOnly,
    Requires,
    Ensures,
    Result,
)
from nagini_contracts.io_contracts import *
from typing import Tuple


@ContractOnly
def read_int(t1: Place) -> Tuple[Place, int]:
    IOExists2(Place, int)(
        lambda t2, value: (
        Requires(
            token(t1, 1) and
            read_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()[0] and
            value == Result()[1]
        ),
        )
    )


@IOOperation
def read_int_io(
        t_pre: Place,
        number: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
