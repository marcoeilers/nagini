from nagini_contracts.contracts import Requires, Predicate
from nagini_contracts.io_contracts import *


def foo() -> None:
    #:: ExpectedOutput(invalid.program:invalid.io_operation.misplaced_property)
    Terminates(False)
