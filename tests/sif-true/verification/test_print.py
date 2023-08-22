# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def foo(i: int) -> None:
    Requires(LowEvent())
    #:: ExpectedOutput(call.precondition:assertion.false)
    print(i)


def foo2(i: int) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    print(6)


class MyObject(object):
    pass


def test(x: int) -> None:
    Requires(LowEvent())
    if x > 0:
      m1 = MyObject()
    m2 = MyObject()
    #:: ExpectedOutput(call.precondition:assertion.false)
    print(str(m2))
