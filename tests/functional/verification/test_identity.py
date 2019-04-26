# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def m() -> None:
    a = ()
    b = ()
    assert a is b

    e = (6,7)
    f = (7,8)
    assert e is not f

    c = (5,)
    d = (5,)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c is d


def m2() -> None:
    a = range(0, 2)
    b = range(0, 3)
    assert a is not b

    c = range(2, 6)
    d = range(2, 6)

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c is d


def m3() -> None:
    a = 'Whatsup'
    assert a is 'Whatsup'

    b = 'as'
    c = 'asd'
    assert b is not c

    d = b + 'd'

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert d is not c