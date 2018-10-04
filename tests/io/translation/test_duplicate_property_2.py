from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    TerminationMeasure(5)
    #:: ExpectedOutput(invalid.program:invalid.io_operation.duplicate_property)
    TerminationMeasure(4)
