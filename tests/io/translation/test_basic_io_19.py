from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    if True:
        #:: ExpectedOutput(invalid.program:invalid.io_operation.misplaced_property)
        Terminates(True)
