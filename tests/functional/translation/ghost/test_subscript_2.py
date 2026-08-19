# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def read_ghost_index(l: List[int], gi: GInt) -> int:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    # The index does not exist at runtime.
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    x = l[gi]
    return x
