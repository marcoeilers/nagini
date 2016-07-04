from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.invalid_postset)
@IOOperation
def read_int_io(
        t_pre1: Place,
        result: int = Result(),
        t_post1: Place = Result(),
        t_post2: Place = Result(),
        ) -> bool:
    Terminates(False)
