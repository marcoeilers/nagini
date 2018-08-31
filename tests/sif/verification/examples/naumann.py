"""
Example from "From coupling relations to mated invariants for checking information flow"
D. A. Naumann
ESORICS 2006
"""
from typing import List, cast

from nagini_contracts.contracts import *

class Node:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)

NodeList = List[Node]

def m(x: int, secret: int, l: List[Node]) -> None:
    Requires(list_pred(l))
    Requires(len(l) == 10)
    Requires(Low(x))
    Requires(Forall(cast(NodeList, l), lambda e: (Acc(e.val), [[e in l]])))
    Ensures(list_pred(l))

    Ensures(Forall(cast(NodeList, l), lambda e: (Acc(e.val), [[e in l]])))

    # Ensures(Forall(range(0, len(l)), lambda k: l[k] in l and l[k].val == x))
    Ensures(Forall(range(0, len(l)), lambda k: l[k] in l and Low(l[k].val)))
    i = 0
    while i < 10:
        Invariant(list_pred(l))
        Invariant(i >= 0 and i <= 10 and len(l) == 10)
        Invariant(Low(i))
        Invariant(Forall(cast(NodeList, l), lambda e: Acc(e.val)))
        Invariant(Low(x))
        # Invariant(Forall(range(0, i), lambda k: (l[k] in l and l[k].val == x, [[l[k]]])))
        Invariant(Forall(range(0, i), lambda k: (l[k] in l and Low(l[k].val), [[l[k]]])))
        l[i].val = x
        i += 1
