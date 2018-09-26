from nagini_contracts.contracts import ContractOnly, Result, Requires
from nagini_contracts.io_contracts import *


@ContractOnly
def test() -> None:
    IOExists1(Place)(
        lambda t: (
            #:: ExpectedOutput(invalid.program:io_existential_var.use_of_undefined)
            Requires(token(t, 1))
        ),
    )

