# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *


class C1:
    pass


class C2(C1):
    pass


@IOOperation
def do_io(
        t1_pre: Place,
        value: C2 = Result(),
        ) -> bool:
    Terminates(False)


@ContractOnly
def test(t1: Place) -> C2:
    IOExists1(C1)(
        lambda value: (
        Requires(
            #:: ExpectedOutput(type.error:Argument 2 to "do_io" has incompatible type "C1"; expected "C2")
            do_io(t1, value)
        ),
        Ensures(
            value == Result()
        ),
        )
    )
