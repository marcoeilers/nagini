from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.invalid_postset)
@IOOperation
def read_int_io(
        t_pre1: Place,
        t_post: Place = Result(),
        result: int = Result(),
        ) -> bool:
    Terminates(False)
