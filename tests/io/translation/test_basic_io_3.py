from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.kwarg)
@IOOperation
def read_int_io(**kwarg) -> bool:
    Terminates(False)
