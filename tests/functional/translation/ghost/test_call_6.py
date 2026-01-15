# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GInt = int
MarkGhost(GInt)

@Ghost
def ghost_calls() -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    gi = ghost_lst([0, 1, ghost(reg_but_ghost_return()), 3])

def reg_but_ghost_return() -> GInt:
    # Do something with potential side-effects
    pass

@Ghost
def ghost(i: int) -> int:
    pass

@Ghost
def ghost_lst(lst: List[int]) -> int:
    pass