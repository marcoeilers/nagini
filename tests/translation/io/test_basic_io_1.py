from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:invalid.io_operation.return_type_not_bool)
@IOOperation
def read_int_io(
        t_pre: Place,
        result: int,
        t_post: Place,
        ) -> None:
    Terminates(False)
