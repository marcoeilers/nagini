# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Optional

from nagini_contracts.contracts import *


def first(x: int, key: None = None) -> int:
    Ensures(Result() == x)
    if key is None:
        return x
    return 0


def forward(x: int, key: None) -> int:
    Ensures(Result() == 3 * x)
    return first(x, key) + first(x, None) + first(x)


class C:
    def __init__(self, start: None = None, stop: None = None) -> None:
        self.n = 0
        Ensures(Acc(self.n) and self.n == 0)

    def m(self, o: Optional[int], k: None) -> int:
        Ensures(Result() == (0 if o is None else o))
        if k is not None:
            return 7
        if o is None:
            return 0
        return o


def client() -> None:
    c = C()
    d = C(None, stop=None)
    assert c.m(None, None) == 0
    assert d.m(4, None) == 4
    assert forward(2, None) == 6
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert first(1) == 2
