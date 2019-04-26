# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def test_abs(x: int) -> None:
    a = -2
    b = abs(a)
    assert b == 2
    c = abs(2+3)
    assert c == 5
    assert abs(x) >= 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert abs(x) > 0

def test_max() -> None:
    assert max(1,max(-3, 6)) == 6
    c = max(2, -5) + max(-3, -2)
    assert c == 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False

def test_min() -> None:
    a = [1,2,3]
    c = min(a)
    e = min(3, 7)
    assert e == 3
    assert c is not 6
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c is not 1