# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List
from nagini_contracts.contracts import *


class Box:
    def __init__(self, n: int) -> None:
        self.n = n
        Ensures(Acc(self.n) and self.n == n)

    def __contains__(self, key: int) -> bool:
        Requires(Acc(self.n, 1/2))
        Ensures(Acc(self.n, 1/2))
        Ensures(Result() == (key == self.n))
        return key == self.n


class PureBox:
    def __init__(self, n: int) -> None:
        self.n = n
        Ensures(Acc(self.n) and self.n == n)

    @Pure
    def __contains__(self, key: int) -> bool:
        Requires(Acc(self.n, 1/2))
        return key == self.n


def method_contains(b: Box, key: int) -> int:
    Requires(Acc(b.n, 1/2))
    Ensures(Acc(b.n, 1/2))
    Ensures(Result() == (0 if key != b.n else 1))
    if key not in b:
        return 0
    return 1


def pure_contains(b: PureBox, key: int) -> None:
    Requires(Acc(b.n, 1/2))
    Ensures(Acc(b.n, 1/2))
    Assert((key not in b) == (key != b.n))
    if key not in b:
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(key == b.n)


def list_contains(xs: List[int], key: int) -> bool:
    Requires(Acc(list_pred(xs)))
    Ensures(Acc(list_pred(xs)))
    Ensures(Result() == (key not in xs))
    return key not in xs
