# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *


@IOOperation
def my_gap_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)

@ContractOnly
def my_gap(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            my_gap_io(t1, t2)
        ),
        Ensures(
            #:: ExpectedOutput(invalid.program:invalid.postcondition.ctoken_not_allowed)
            ctoken(t2) and # ctoken in postcondition is unsound.
            t2 == Result()
        ),
    ))
