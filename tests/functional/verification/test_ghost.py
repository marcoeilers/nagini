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
        Ensures(self.count == 0)  # type: ignore
        self.count = 0

    def bump(self) -> None:
        Requires(MustTerminate(1))
        Requires(Acc(self.count))
        Ensures(Acc(self.count) and self.count == Old(self.count) + 1)
        self.count = self.count + 1


@Ghost
def make_tracker() -> Tracker:
    Requires(MustTerminate(2))
    Ensures(Acc(Result().count) and Result().count == 0)
    return Tracker()


@Ghost
@Pure
def double(i: int) -> int:
    return 2 * i


def counted_sum(l: List[int]) -> Tuple[int, GIdx]:
    Requires(Acc(list_pred(l), 1/2))
    Ensures(Acc(list_pred(l), 1/2))
    Ensures(Result()[1] == len(l))
    total = 0
    steps: GIdx = 0
    i = 0
    while i < len(l):
        Invariant(Acc(list_pred(l), 1/2) and 0 <= i and i <= len(l))
        Invariant(steps == i)
        total += l[i]
        steps += 1
        i += 1
    return total, steps


def client(l: List[int]) -> int:
    Requires(Acc(list_pred(l), 1/2))
    Ensures(Acc(list_pred(l), 1/2))
    t = make_tracker()
    t.bump()
    Assert(t.count == 1)
    n: GIdx = 0
    s, n = counted_sum(l)
    Assert(n == len(l))
    gd: GIdx = double(n)
    Assert(gd == 2 * len(l))
    return s


def client_fail(l: List[int]) -> int:
    Requires(Acc(list_pred(l), 1/2))
    Ensures(Acc(list_pred(l), 1/2))
    n: GIdx = 0
    s, n = counted_sum(l)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(n == len(l) + 1)
    return s
