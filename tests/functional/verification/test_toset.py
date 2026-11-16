# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Dict, Set
from nagini_contracts.contracts import *


def set_view(s: Set[int]) -> None:
    Requires(Acc(set_pred(s)))
    Requires(3 not in s)
    before = ToSet(s)  # type: PSet[int]
    Assert(len(before) == len(s))
    Assert(Forall(int, lambda x: ((x in before) == (x in s), [[x in before]])))
    Assert(Forall(ToSeq(s), lambda x: (x in before, [])))
    s.add(3)
    Assert(3 in ToSet(s))
    Assert(ToSet(s) == before + PSet(3))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(ToSet(s) == before)


def key_view(d: Dict[int, int]) -> None:
    Requires(Acc(dict_pred(d)))
    Requires(7 not in d)
    keys = ToSet(d)  # type: PSet[int]
    Assert(len(keys) == len(d))
    Assert(Forall(int, lambda k: ((k in keys) == (k in d), [[k in keys]])))
    d[7] = 1
    Assert(7 in ToSet(d))
    Assert(ToSet(d) == keys + PSet(7))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(len(ToSet(d)) == len(keys))


def pset_passthrough(p: PSet[int]) -> None:
    Assert(ToSet(p) == p)
