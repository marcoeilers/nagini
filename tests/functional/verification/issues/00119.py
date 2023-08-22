# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class A:
    def __init__(self, value: int) -> None:
        self.value = value  # type: int
        Ensures(Acc(self.value) and self.value is value)


def test() -> None:
    Assert(A(5).value == 5)


def test2() -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(A(3).value == 5)