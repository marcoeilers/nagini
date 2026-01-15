# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

def reg_calls(gi: GInt) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    i = reg(gi, 0)

def reg(i: int, gi: GInt) -> int:
    # Do something with potential side-effects
    pass