from py2viper_contracts.contracts import Ensures
from py2viper_contracts.io import *
from typing import Tuple, Callable


def test() -> Place:
    IOExists = lambda t2: (
        Ensures(
            #:: ExpectedOutput(invalid.program:io_existential_var.use_of_undefined)
            Result() == t2 and
            token(t2)
        )
    )   # type: Callable[[Place], bool]
