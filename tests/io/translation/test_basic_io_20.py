# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Predicate
from nagini_contracts.io_contracts import *
from typing import Tuple


def test() -> Place:
    IOExists1(Place)(
        lambda t2: (
        Ensures(
            t2 == Result() and
            token(t2)
        ),
        )
    )

    #:: ExpectedOutput(type.error:Name 't2' is not defined)
    a = t2
