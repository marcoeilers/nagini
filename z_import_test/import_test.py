
from nagini_contracts.contracts import *

GBool = bool
MarkGhost(GBool)

@Ghost
def ghost_func(i: int) -> int:
    return i