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
        value: C1 = Result(),
        ) -> bool:
    Terminates(False)


@ContractOnly
def test(t1: Place) -> C1:
    IOExists1(C2)(
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
