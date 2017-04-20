from nagini_contracts.contracts import *
from typing import Generic, TypeVar, List, Tuple


def m(l: List[int]) -> List[bool]:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(l))
    Ensures(Forall(range(0, len(Result())), lambda i: (Result()[i] == (l[i] != 5) , [])))
    return [e != 5 for e in l]


def m2(l: List[int]) -> List[bool]:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(l))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Forall(range(0, len(Result())), lambda i: (Result()[i] == (l[i] != 4) , [])))
    return [e != 5 for e in l]


def m3() -> None:
    a = [1,2,3,4]
    b = [el % 2 == 0 for el in a]
    assert b[1]
    assert b[3]
    assert not b[0]
    assert not b[2]


def m4() -> None:
    a = [1,2,3,4]
    b = [el % 2 == 0 for el in a]
    assert b[1]
    assert b[3]
    assert not b[0]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b[2]
