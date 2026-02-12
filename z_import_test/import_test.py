
from nagini_contracts.contracts import *
from typing import List

GBoolList = List[bool]
MarkGhost(GBoolList)

@Ghost
def ghost_func(i: int) -> int:
    return i