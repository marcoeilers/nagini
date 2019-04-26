# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Ensures, Implies, Result
from nagini_contracts.io_contracts import *
from typing import Tuple, Callable


def test(x: bool) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Ensures(
            #:: ExpectedOutput(invalid.program:io_existential_var.use_of_undefined)
            Implies(x, t2 == Result())
        ),
        )
    )
