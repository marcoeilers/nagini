from py2viper_contracts.contracts import *

@Pure
def inc(x: int) -> int:
    return x + 1

def test_getitem() -> None:
    a = 1
    b = 2
    c = inc(a + b)
    l = [a, b, c]
    d = l[2]
    Assert(c == d)
    Assert(d == 4)


def test_setitem() -> None:
    l = [1, 2, 3]
    l[0] = inc(l[1] + l[2])
    Assert(l[0] == 7)
