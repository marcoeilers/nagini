from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


@Predicate
def foo() -> bool:
    #:: ExpectedOutput(invalid.program:invalid.io_operation.misplaced_property)
    Terminates(False)
