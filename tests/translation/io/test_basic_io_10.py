#:: IgnoreFile(/py2viper/issue/35/)
from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *


@IOOperation
#:: ExpectedOutput(type.error:Encountered Any type, type annotation missing?)
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ):
    Terminates(False)
