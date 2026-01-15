# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GInt = int
MarkGhost(GInt)

def main(i: int, gi: GInt) -> List[int]:
    lst: List[int] = []
    while i < 5:
        i += 1
        if gi == 6:
            #:: ExpectedOutput(invalid.program:invalid.ghost.continue)
            continue
        lst.append(i)
    
    return lst
