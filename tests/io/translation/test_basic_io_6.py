from nagini_contracts.contracts import Requires, Predicate, Result
from nagini_contracts.io_contracts import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.invalid_preset)
@IOOperation
def read_int_io(
        t_pre1: Place,
        t_pre2: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
