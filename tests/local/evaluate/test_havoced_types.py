# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Optional


class A:
    def __init__(self) -> None:
        self.a = 15

class B:
    pass


def m(l: List[A]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(Forall(l, lambda a: (Acc(a.a), [])))
    Requires(len(l) > 2)
    myb = l[0]
    i = 0
    while i < len(l):
        Invariant(i >= 0)
        Invariant(Acc(list_pred(l), 1/2))
        Invariant(Forall(l, lambda a: (Acc(a.a, 1/4), [])))
        Invariant(myb in l)
        assert isinstance(myb, A)
        assert isinstance(myb.a, int)
        myb = l[i]
        i += 1


def m2(l: List[A]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(Forall(l, lambda a: (Acc(a.a), [])))
    Requires(len(l) > 2)
    myb = l[0]
    i = 0
    while i < len(l):
        Invariant(i >= 0)
        Invariant(Acc(list_pred(l), 1/2))
        Invariant(Forall(l, lambda a: (Acc(a.a, 1/4), [])))
        Invariant(myb in l)
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert isinstance(myb, B) or isinstance(myb.a, bool)
        myb = l[i]
        i += 1


def m3(l: List[A]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(Forall(l, lambda a: (Acc(a.a), [])))
    Requires(len(l) > 2)
    myb = l[0]
    i = 0
    for item in l:
        Invariant(i >= 0)
        Invariant(Acc(list_pred(l), 1/2))
        Invariant(Forall(l, lambda a: (Acc(a.a, 1/4), [])))
        Invariant(myb in l)
        assert isinstance(myb, A)
        assert isinstance(myb.a, int)
        assert isinstance(item, A)
        assert isinstance(item.a, int)
        myb = item
        i += 1


def m4(l: List[A]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(Forall(l, lambda a: (Acc(a.a), [])))
    Requires(len(l) > 2)
    myb = l[0]
    i = 0
    for item in l:
        Invariant(i >= 0)
        Invariant(Acc(list_pred(l), 1/2))
        Invariant(Forall(l, lambda a: (Acc(a.a, 1/4), [])))
        Invariant(myb in l)
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert isinstance(myb, B) or isinstance(myb.a, bool) or isinstance(item, B) or isinstance(item.a, bool)
        myb = item
        i += 1