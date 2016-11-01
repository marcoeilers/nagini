from py2viper_contracts.contracts import Requires, Predicate, Result
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.invalid_preset)
@IOOperation
def read_int_io(
        t_pre1: Place,
        t_pre2: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
