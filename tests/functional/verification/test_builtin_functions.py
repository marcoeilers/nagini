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