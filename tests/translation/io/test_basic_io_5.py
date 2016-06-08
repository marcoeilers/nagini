from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.invalid_preset)
@IOOperation
def read_int_io(
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
