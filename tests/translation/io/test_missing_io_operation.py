#:: IgnoreFile(/py2viper/issue/29/)
from py2viper_contracts.contracts import (
    Requires,
    Ensures,
)
from py2viper_contracts.io import *
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
