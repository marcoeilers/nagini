# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Generic, TypeVar, List, Tuple


def m(l: List[int]) -> List[bool]:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(l))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(Result()), Result()[i] == (l[i] != 5)), [[l[i]]])))
    #:: ExpectedOutput(invalid.program:impure.list.comprehension.body)
    return [m2(e) for e in l]


def m2(e: int) -> bool:
    return e != 5
