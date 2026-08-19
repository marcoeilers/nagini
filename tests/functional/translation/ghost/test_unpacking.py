# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Tuple

GPair = Tuple[int, int]
MarkGhost(GPair)


def unpack_ghost_pair(p: GPair) -> None:
    ga: GInt = 0
    gb: GInt = 0
    ga, gb = p

def unpack_regular(l: List[Tuple[int, int]]) -> int:
    Requires(Acc(list_pred(l)) and len(l) > 0)
    Ensures(Acc(list_pred(l)))
    a, b = l[0]
    return a + b
