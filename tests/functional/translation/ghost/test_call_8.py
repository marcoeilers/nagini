# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Ghost
def ghost_calls(gi: int) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    glst = [1, 2, ghost(impure_reg(gi)), 4]

@Ghost
def ghost(gi: int) -> int:
    return gi

def impure_reg(gi: GInt) -> GInt:
    # Do something with potential side-effects
    return gi+1