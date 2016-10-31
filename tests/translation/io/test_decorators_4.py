from py2viper_contracts.contracts import Ghost, Result
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:decorators.incompatible)
@Ghost
@IOOperation
def read_int_io(
        t_pre1: Place,
        res: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
