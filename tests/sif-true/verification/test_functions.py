# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def func1() -> int:
    Ensures(Result() == 15)
    return 15


@Pure
def func2() -> bool:
    Ensures(Result() == False)
    return False


@Pure
def func3(a: int) -> int:
    Ensures(Result() == a)
    return a


@Pure
def func4(a: int) -> int:
    Ensures(Result() == a + 42)
    return a + 42


@Pure
def func5(a: int, b: int, c: bool) -> bool:
    return (a + b > 42) == c


@Pure
def func6(a: int) -> bool:
    # Requires(Low(a))
    b = a + 42
    if b > 50:
        c = b < 100
        return c
    return a < 10


@Pure
def func7(a: int) -> int:
    Requires(a > 3)
    Ensures(Result() > 42)
    b = 2
    c = a + b
    if c > 5:
        c += 1
        if c > 10:
            c -= 1
    else:
        c -= 1
    return c + 42


@Pure
def func8(a: int) -> int:
    Requires(a > 3)
    Ensures(Result() > 42)
    b = func7(func7(a))
    return b


@Pure
def square(a: int) -> int:
    Ensures(Result() >= 0)
    return a * a


@Pure
def foo(a: int) -> int:
    Ensures(Implies(a != 0, Result() > 0))
    Ensures(Implies(a < 0, Result() == square(square(a))))
    if a < 0:
        b = square(square(a))
    else:
        b = square(a)
    return b


def bar(a: int) -> int:
    Requires(a > 0)
    Requires(not func2())
    Ensures(Result() > 0)
    return foo(a)
