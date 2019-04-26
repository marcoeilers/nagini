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


@ContractOnly
def test() -> C2:
    IOExists1(C1)(
        lambda value: (
        Ensures(
            #:: ExpectedOutput(invalid.program:invalid.io_existential_var.defining_expression_type_mismatch)
            value == Result() and
            value == True
        ),
        )
    )
