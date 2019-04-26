# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def identity(a: int) -> int:
    return a


def test_list() -> None:
    r = [1, 2, 3]
    Assert(Forall(r, lambda i: (identity(i) > 0, [])))


def test_list_2() -> None:
    r = [1, -2, 3]
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(r, lambda i: (identity(i) > 0, [])))
