# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def seq_is_ghost(s: PSeq[int]) -> PSeq[int]:
    return s

def set_is_ghost(s: PSet[int]) -> PSet[int]:
    return s

def multiset_is_ghost(s: PMultiset[int]) -> PMultiset[int]:
    return s

def local_pseq(l: List[int]) -> None:
    Requires(Acc(list_pred(l)))
    # The type of the local variable is ghost, so no annotation is needed.
    s = ToSeq(l)
    gi: GInt = len(s)
