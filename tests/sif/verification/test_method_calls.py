from nagini_contracts.contracts import *


def foo(x: int) -> int:
    Requires(x >= 0)
    Requires(Low(x >= 0))
    Ensures(Result() == 2 * x)
    Ensures(Low(Result() == 2 * x))
    return 2 * x


def bar(x: int) -> int:
    Requires(x > 2)
    Requires(Low(x > 2))
    Ensures(Result() == x - 2)
    Ensures(Low(Result() == x - 2))
    return x - 2


class A:
    def __init__(self, a: int) -> None:
        Ensures(Acc(self.a))  # type: ignore
        Ensures(self.a == a)  # type: ignore
        self.a = a

    def m1(self, x: int) -> int:
        Ensures(Result() == x)
        return x

    def m2(self, x: int) -> bool:
        Requires(Acc(self.a, 1/2))
        Ensures(Acc(self.a, 1/2))
        Ensures(Result() == (x > self.a))
        return x > self.a


def main() -> None:
    x = 25 * foo(bar(5))
    a = A(x)
    b = a.m2(a.m1(x))
    Assert(not b)
    c = A(2).m1(x)
    Assert(c == 150)
