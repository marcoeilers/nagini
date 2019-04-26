# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def a() -> None:
    a = [1, 2]
    b = [True]
    Assert(Forall(a, lambda x: (x > 0, [])) and Forall(b, lambda x: (x, [])))


def test_nested_forall() -> None:
    a = range(1, 3)
    b = range(1, 6)
    c = range(4, 7)
    Assert(Forall(a, lambda x: (Forall(b, lambda y: (Implies(x == y, Forall(c, lambda x: (x > y, []))), [])), [])))


def test_nested_forall_2() -> None:
    a = range(1, 5)
    b = range(1, 6)
    c = range(4, 7)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(a, lambda x: (Forall(b, lambda y: (Implies(x == y, Forall(c, lambda x: (x > y, []))), [])), [])))
