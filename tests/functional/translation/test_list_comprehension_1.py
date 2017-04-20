from nagini_contracts.contracts import *
from typing import Generic, TypeVar, List, Tuple


def m(l: List[int]) -> List[bool]:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(l))
    Ensures(Forall(range(0, len(Result())), lambda i: (Result()[i] == (l[i] != 5) , [])))
    #:: ExpectedOutput(invalid.program:impure.list.comprehension.body)
    return [m2(e) for e in l]


def m2(e: int) -> bool:
    return e != 5
