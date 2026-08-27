# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def read_ghost_index(l: List[int], gi: GInt) -> None:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    # Indexing with a ghost value yields a ghost value.
    gx: GInt = l[gi]

def slices(l: List[int], gi: GInt) -> None:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    a = l[1:2]
    gb: PSeq[int] = ToSeq(l)
    gc: GInt = gb[gi]
