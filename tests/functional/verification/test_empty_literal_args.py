# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Dict, Set, Optional


def takes_list(l: List[int]) -> int:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)) and Result() == len(l))
    return len(l)


def takes_dict(d: Dict[str, int]) -> None:
    Requires(Acc(dict_pred(d)))


def call_list() -> None:
    r = takes_list([])


def call_dict() -> None:
    takes_dict({})


def call_kw() -> None:
    takes_list(l=[])


class C:
    def __init__(self, xs: List[int]) -> None:
        Requires(Acc(list_pred(xs)))
        self.xs = xs
        Ensures(Acc(self.xs) and self.xs is xs)


def ctor() -> None:
    c = C([])


def via_local() -> None:
    e: List[int] = []
    takes_list(e)


def takes_opt(l: Optional[List[int]]) -> None:
    Requires(Implies(l is not None, Acc(list_pred(l))))


class K:
    def m(self, xs: List[int]) -> None:
        Requires(Acc(list_pred(xs)))

    @staticmethod
    def s(a: int, xs: List[str]) -> None:
        Requires(Acc(list_pred(xs)))


def call_methods(k: K) -> None:
    takes_opt([])
    k.m([])
    K.s(1, [])
    k.m(xs=[])


def takes_set(s: Set[int]) -> None:
    Requires(Acc(set_pred(s)))


def takes_seq(s: PSeq[int]) -> None:
    Requires(len(s) == 0)


def call_constructors() -> None:
    takes_set(set())
    takes_seq(PSeq())
    takes_set(s=set())


def takes_obj(o: object) -> None:
    pass


def no_parameter_type() -> None:
    # No typed context: the literal is a List[object], as before.
    takes_obj([])
    Assert(len([]) == 0)
