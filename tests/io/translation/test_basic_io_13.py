from nagini_contracts.contracts import Requires, Predicate
from nagini_contracts.io import *


@Predicate
def foo() -> bool:
    #:: ExpectedOutput(invalid.program:invalid.io_operation.misplaced_property)
    Terminates(False)
