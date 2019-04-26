# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def rangetest() -> None:
    a = range(0, 5)
    Assert(a[2] == 2)
    Assert(3 in a)
    Assert(7 not in a)
    Assert(5 not in a)
    Assert(Forall(a, lambda x: (x < 5, [])))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(a, lambda x: (x < 4, [])))


def rangetest2() -> None:
    a = range(0, 5)
    for i in a:
        assert i < 6
    assert i == 4
    for b in a:
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert b > 2
