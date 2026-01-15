# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GInt = int
MarkGhost(GInt)

@Ghost
def ghost_calls(lst: List[int]) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    i = [pure_reg(e) for e in lst]

@Pure
def pure_reg(gi: GInt) -> GInt:
    # Do something with potential side-effects
    return gi+1