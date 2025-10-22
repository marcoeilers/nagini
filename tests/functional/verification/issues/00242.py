# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


def test1() -> None:
    a = int.__add__(5, 4)
    assert a == 9

def test1f() -> None:
    a = int.__add__(5, 4)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a == 5

def test2() -> None:
    x = [1]
    list.append(x, 4)
    assert len(x) == 2

def test2f() -> None:
    x = [1]
    list.append(x, 4)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(x) == 1