# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional, List, cast


def test_range() -> None:
    r = range(3, 6)
    Assert(5 in r)
    Assert(Exists(r, lambda i: i > 4))


def test_range_2() -> None:
    r = range(3, 6)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Exists(r, lambda i: i > 6))


def test_list() -> None:
    r = [3,4,5]
    Assert(5 in r)
    Assert(Exists(r, lambda i: i > 4))


def test_list_2() -> None:
    r = [3,4,5]
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Exists(r, lambda i: (i > 5)))


def test_type_quantification() -> None:
    r = [3, 4, 5]
    Assert(r[1] > 3)
    Assert(Exists(int, lambda i: (i >= 0 and i < len(r) and r[i] > 3, [[r[i]]])))


def test_type_quantification_2() -> None:
    r = [3, 4, 5]
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Exists(int, lambda i: (i >= 0 and i < len(r) and r[i] > 6, [[r[i]]])))


def foo(l: Optional[List[int]]) -> None:
    Requires(l is not None)
    Requires(list_pred(l))
    Requires(Exists(cast(List[int], l), lambda el: el > 5))

    Assert(Exists(l, lambda el: el > 5))