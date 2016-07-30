from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.vararg)
@IOOperation
def read_int_io(*args) -> bool:
    Terminates(False)
