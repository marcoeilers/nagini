from nagini_contracts.contracts import Requires, Predicate
from nagini_contracts.io_contracts import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.kwarg)
@IOOperation
def read_int_io(**kwarg) -> bool:
    Terminates(False)
