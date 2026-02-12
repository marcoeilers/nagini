# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def reg_calls(gi: GInt) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    t = reg_mixed_return()

def reg_mixed_return() -> Tuple[Tuple[int, int], Tuple[GInt, GInt]]:
    pass
