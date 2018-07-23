from nagini_contracts.contracts import Requires, Predicate, Result
from nagini_contracts.io_contracts import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.invalid_postset)
@IOOperation
def read_int_io(
        t_pre1: Place,
        result: int = Result(),
        t_post1: Place = Result(),
        t_post2: Place = Result(),
        ) -> bool:
    Terminates(False)
