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
        value: int = Result(),
        ) -> bool:
    Terminates(False)


@ContractOnly
def test(t1: Place) -> int:
    IOExists1(bool)(
        lambda value: (
        Requires(
            #:: ExpectedOutput(invalid.program:invalid.io_existential_var.defining_expression_type_mismatch)
            do_io(t1, value)
        ),
        Ensures(
            value == Result()
        ),
        )
    )
