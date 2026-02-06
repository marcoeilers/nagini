# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GInt = int
MarkGhost(GInt)

def main(lst: List[int]) -> None:
    gi: GInt = 0
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    i, *s, gi = lst
