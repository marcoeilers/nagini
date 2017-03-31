from nagini_contracts.contracts import Result
from nagini_contracts.io import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)
    #:: ExpectedOutput(invalid.program:invalid.io_operation.duplicate_property)
    Terminates(True)
