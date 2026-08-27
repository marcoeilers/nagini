# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Tuple


def reg_calls(gi: GInt) -> None:
    g_tuple: Tuple[GInt, GInt] = (0,0)
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    reg(*g_tuple)

def reg(i: int, gi: GInt) -> int:
    # Do something with potential side-effects
    pass
