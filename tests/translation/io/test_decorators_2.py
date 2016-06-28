from py2viper_contracts.contracts import Predicate
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:decorators.incompatible)
@IOOperation
@Predicate
def read_int_io(
        t_pre1: Place,
        res: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
