# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires
from nagini_contracts.io_contracts import *
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
