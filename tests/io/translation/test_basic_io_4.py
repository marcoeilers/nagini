from nagini_contracts.contracts import Requires, Predicate
from nagini_contracts.io_contracts import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.default_argument)
@IOOperation
def read_int_io(x: int = 1) -> bool:
    Terminates(False)
