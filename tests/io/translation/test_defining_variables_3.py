from nagini_contracts.contracts import Ensures, Result
from nagini_contracts.io import *
from typing import Tuple, Callable


def test() -> Place:
    IOExists1(Place)(
        lambda t2: (
        Ensures(
            #:: ExpectedOutput(invalid.program:io_existential_var.use_of_undefined)
            token(t2) and
            t2 == Result()
        ),
        )
    )
