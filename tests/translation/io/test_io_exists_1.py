from py2viper_contracts.contracts import Requires
from py2viper_contracts.io import *
from typing import Tuple


def test(t1: Place) -> None:
    IOExists1(Place)(
        lambda t2: (
            #:: ExpectedOutput(invalid.program:invalid.ioexists.misplaced)
            IOExists1(int)(
                lambda value: Requires(True)
            )
        )
    )
