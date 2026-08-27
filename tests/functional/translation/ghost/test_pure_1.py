# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


@Predicate
def valid(l: List[int]) -> bool:
    return Acc(list_pred(l))


@Ghost
@Pure
def all_positive(l: List[int]) -> bool:
    Requires(Acc(list_pred(l), 1/2))
    # A pure function whose body is a specification expression has to be ghost.
    return Forall(int, lambda i: Implies(0 <= i and i < len(l), l[i] > 0))


@Pure
def unfolded(l: List[int]) -> int:
    Requires(valid(l))
    # Unfolding and Implies denote plain values, so this function stays regular.
    return Unfolding(valid(l), len(l))


def client(l: List[int]) -> int:
    Requires(valid(l))
    Ensures(valid(l))
    return unfolded(l)
