from py2viper_contracts.contracts import Predicate, Result
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:decorators.incompatible)
@Predicate
@IOOperation
def read_int_io(
        t_pre1: Place,
        res: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
