# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GInt = int
MarkGhost(GInt)

def main(gi: GInt, g_lst: List[GInt]) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    g_lst[0] = gi
