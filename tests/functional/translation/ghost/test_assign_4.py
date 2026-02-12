# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Tuple


def main(g_lst: List[GInt]) -> None:
    gi: GInt = 0
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    (i, j), (gi, g_lst[0]) = reg_mixed_return()

def reg_mixed_return() -> Tuple[Tuple[int, int], Tuple[GInt, GInt]]:
    pass
