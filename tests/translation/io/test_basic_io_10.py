from py2viper_contracts.contracts import Result
from py2viper_contracts.io import *


@IOOperation #:: ExpectedOutput(type.error:Encountered Any type. Type annotation missing?)


def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ):
    Terminates(False)
