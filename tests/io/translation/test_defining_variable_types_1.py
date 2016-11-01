from py2viper_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from py2viper_contracts.io import *


@ContractOnly
def test() -> int:
    IOExists1(bool)(
        lambda value: (
        Ensures(
            #:: ExpectedOutput(invalid.program:invalid.io_existential_var.defining_expression_type_mismatch)
            value == Result() and
            value == True
        ),
        )
    )
