from py2viper_contracts.contracts import *
from typing import List, Tuple


def nested_main() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(list_pred(l)), [])))
        c.append(7)
    a.append(4)