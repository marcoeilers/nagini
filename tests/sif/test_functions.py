from py2viper_contracts.contracts import *


@Pure
def func1() -> int:
    return 15


@Pure
def func2() -> bool:
    return False


@Pure
def func3(a: int) -> int:
    return a


@Pure
def func4(a: int) -> int:
    return a + 42


@Pure
def func5(a: int, b: int, c: bool) -> bool:
    return (a + b > 42) == c


@Pure
def func6(a: int) -> bool:
    b = a + 42
    if b > 50:
        c = b < 100
        return c
    return a < 10


@Pure
def func7(a: int) -> int:
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
    b = func7(func7(a))
    return b