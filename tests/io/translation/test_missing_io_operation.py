# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(29)
from nagini_contracts.contracts import (
    Requires,
    Ensures,
)
from nagini_contracts.io_contracts import *
from typing import Tuple


def read_int(t1: Place) -> None:
    IOExists2(Place, int)(
        lambda t2, value: (
        Requires(
            token(t1) and
            read_int_io(t1, value, t2)
        ),
        )
    )
