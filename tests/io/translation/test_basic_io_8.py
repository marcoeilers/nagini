from nagini_contracts.contracts import Requires, Predicate, Result
from nagini_contracts.io_contracts import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.invalid_postset)
@IOOperation
def read_int_io(
        t_pre1: Place,
        t_post: Place = Result(),
        result: int = Result(),
        ) -> bool:
    Terminates(False)
