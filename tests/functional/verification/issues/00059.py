# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Invariant,
    list_pred,
    Requires,
)
from typing import List


def test1(a: List[int]) -> None:
    Requires(Acc(list_pred(a)))
    Ensures(Acc(list_pred(a)))
    for i in a:
        pass


def test2() -> None:
    a = [1, 2, 3]
    for i in a:
        pass
    Assert(Acc(list_pred(a)))


def test3() -> None:
    a = [1, 2, 3]
    b = [1, 2, 3]
    for i in a:
        Invariant(Acc(list_pred(b)))
        for j in b:
            pass


def test4(a: List[int], b: List[int]) -> None:
    Requires(Acc(list_pred(a)))
    Requires(Acc(list_pred(b)))
    for i in a:
        Invariant(Acc(list_pred(b)))
        for j in b:
            pass
