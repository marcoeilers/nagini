from nagini_contracts.contracts import Requires, Implies
from nagini_contracts.io_contracts import *


@IOOperation
def test_io(
        t_pre: Place,
        b: bool,
        ) -> bool:
    Terminates(True)
    return IOExists1(int)(
        #:: ExpectedOutput(invalid.program:invalid.io_operation.body.use_of_undefined_existential)
        lambda value: value == 2
        )
