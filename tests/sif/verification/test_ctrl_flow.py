from nagini_contracts.contracts import *


@Pure
def cond(a: int) -> bool:
    return a > 42


def foo(a: int) -> int:
    Requires(Low(a))
    Ensures(Implies(cond(a), Result() == a + 1))
    Ensures(Implies(not cond(a), Result() == a + 2))
    if cond(a):
        b = inc(a)
    else:
        b = inc(inc(a))

    return b


def inc(a: int) -> int:
    Ensures(Result() == a + 1)
    return a + 1


def low(a: int, secret: bool) -> None:
    Requires(Low(a))
    if secret:
        a = 0
        return
    Assert(Low(a))
