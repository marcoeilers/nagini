from py2viper_contracts.contracts import NotPreservingTL
from py2viper_contracts.io import *


#:: ExpectedOutput(invalid.program:decorators.incompatible)
@NotPreservingTL
@IOOperation
def read_int_io(
        t_pre1: Place,
        res: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
