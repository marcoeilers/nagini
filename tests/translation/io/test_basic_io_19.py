from py2viper_contracts.contracts import Result
from py2viper_contracts.io import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    if True:
        #:: ExpectedOutput(invalid.program:invalid.io_operation.misplaced_property)
        Terminates(True)
