# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


def literal() -> None:
    a = 1.0
    b = 2.0
    c = 1.0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert (a is b) or (a is c)


def operators() -> None:
    a = 1.0
    b = 2.0
    c = a + b
    d = a * b
    e = a > b
    f = a <= b
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert d == c


def float_int_div(a: float, c: bool) -> None:
    a = 3
    b = 12.0
    if c:
        b = 12
    if c:
        d = 12 / a
        assert d == 4
    a = 0
    if c:
        #:: ExpectedOutput(application.precondition:assertion.false)
        d = 12 / a


def int_div() -> None:
    a = 15
    b = 3
    c = 4
    d = a / b
    e = a / c
    assert isinstance(d, int)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(e, int)


def float_div(a: float, b: float) -> None:
    #:: ExpectedOutput(application.precondition:assertion.false)|ExpectedOutput(carbon)(application.precondition:assertion.false)
    c = a / b