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
def do_io(
        t1_pre: Place,
        value: bool = Result(),
        ) -> bool:
    Terminates(False)


@ContractOnly
def test(t1: Place) -> bool:
    IOExists1(int)(
        lambda value: (
        Requires(
            #:: ExpectedOutput(type.error:Argument 2 to "do_io" has incompatible type "int"; expected "bool")
            do_io(t1, value)
        ),
        Ensures(
            value == Result()
        ),
        )
    )
