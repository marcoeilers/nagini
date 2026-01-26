# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def sum_sorted_test() -> None:
    l = [3, 2]
    l2 = sorted(l)
    l3 = sum(l)
    l4 = sorted([2])
    Assert(l3 == 5)
    Assert(l2[0] <= l2[1])
    Assert(l4[0] == 2)
    Assert(sum(l) == sum(l2))
    Assert(l[0] >= l2[0])
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(False)


def sum_test(l1: List[int], l2: List[int]) -> None:
    Requires(list_pred(l1) and list_pred(l2))
    s3 = sum(l1) + sum(l2)
    l3 = l1 + l2
    Assert(s3 == sum(l3))
    if len(l1) > 0:
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(sum(l1) > 0)


def sorted_test(l1: List[int], l2: List[int]) -> None:
    Requires(list_pred(l1) and list_pred(l2))
    l3 = sorted(l1)
    Assert(l3 is not l2)
    Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(l3) - 1, l3[i] <= l3[i + 1]), [[l3[i]]])))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(l3) - 1, l3[i] < l3[i + 1]), [[l3[i]]])))
