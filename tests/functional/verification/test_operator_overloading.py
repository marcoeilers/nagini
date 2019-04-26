# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Container:
    def __init__(self, v: int) -> None:
        Ensures(Acc(self.value) and self.value == v)  # type: ignore
        self.value = v

    def __add__(self, other: 'Container') -> 'Container':
        Requires(Acc(self.value, 1/100))
        Requires(Acc(other.value, 1/100))
        Ensures(Acc(self.value, 1 / 100))
        Ensures(Acc(other.value, 1 / 100))
        Ensures(Acc(Result().value))
        Ensures(Result().value == self.value + other.value)
        res = Container(self.value + other.value)
        return res

    @Pure
    def __mul__(self, other: 'Container') -> int:
        Requires(Acc(self.value, 1 / 100))
        Requires(Acc(other.value, 1 / 100))
        Ensures(Result() == self.value * other.value)
        return self.value * other.value


def client() -> None:
    c1 = Container(5)
    c3 = Container(6)

    c4 = c1 + c3
    assert c4.value == 11
    assert c1 * c3 == 30
    c4 += c3
    assert c4.value == 17
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
