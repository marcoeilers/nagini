from py2viper_contracts.contracts import (
    Assert,
    Seq,
)


class C:
    pass


def test() -> None:
    s = Seq(1, 2, 3)
    i = s[3]
    s2 = s + Seq(4)
    s4 = s2.set(1, 6)
    Assert(s4[1] == 6)
    Assert(len(s4) == 4)
    Assert(s4[2] == 3)
    Assert(4 in s2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(4 not in s4)


def test_2() -> None:
    c1 = C()
    c2 = C()
    c3 = C()
    c4 = C()
    c6 = C()
    s = Seq(c1, c2, c3)
    i = s[3]
    s2 = s + Seq(c4)
    s4 = s2.set(1, c6)
    Assert(s4[1] == c6)
    Assert(len(s4) == 4)
    Assert(s4[2] == c3)
    Assert(c4 in s2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c4 not in s4)
