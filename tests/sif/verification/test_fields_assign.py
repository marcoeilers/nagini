# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        self.a = 0
        self.b = 0

    def foo(self, a: int, b: int, c: int) -> int:
        Requires(Acc(self.a) and Acc(self.b))
        Ensures(Acc(self.a) and Acc(self.b))
        Ensures(Result() == a + b)
        self.a = a + c
        self.b = b - c

        return self.a + self.b
