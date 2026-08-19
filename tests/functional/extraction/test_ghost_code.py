# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import List, Tuple

GIdx = int
MarkGhost(GIdx)


@Ghost
class Tracker:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.count))  # type: ignore
        self.count = 0

    def bump(self) -> None:
        Requires(MustTerminate(1))
        Requires(Acc(self.count))
        Ensures(Acc(self.count) and self.count == Old(self.count) + 1)
        self.count = self.count + 1


@Ghost
def make_tracker() -> Tracker:
    Requires(MustTerminate(2))
    Ensures(Acc(Result().count))
    return Tracker()


@Predicate
def valid(l: List[int]) -> bool:
    return Acc(list_pred(l))


@ContractOnly
def declared(i: int, gi: GIdx) -> int:
    Requires(i > 0)
    Ensures(Result() > 0)


def counted_sum(l: List[int]) -> Tuple[int, GIdx]:
    Requires(Acc(list_pred(l), 1/2))
    Ensures(Acc(list_pred(l), 1/2))
    total = 0
    steps: GIdx = 0
    i = 0
    while i < len(l):
        Invariant(Acc(list_pred(l), 1/2) and 0 <= i and i <= len(l))
        total += l[i]
        steps += 1
        i += 1
    return total, steps


def client(l: List[int]) -> int:
    Requires(Acc(list_pred(l), 1/2))
    Ensures(Acc(list_pred(l), 1/2))
    t = make_tracker()
    t.bump()
    n: GIdx = 0
    s, n = counted_sum(l)
    Assert(n >= 0)
    return declared(s + 1, n)


g_counter: GIdx = 0
r_counter: int = 0


def globals_stay_regular() -> int:
    return r_counter


@Ghost
class GhostOnly:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.v))  # type: ignore
        self.v = 0


def ghost_class_argument(g: GhostOnly, i: int) -> int:
    return i
