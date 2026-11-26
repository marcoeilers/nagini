# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import ClassVar, Final

from nagini_contracts.contracts import *


class Config:
    limit: int = 10
    step: ClassVar[int] = 2
    top: Final = 3
    plain = 5

    def __init__(self) -> None:
        self.n = 0
        Ensures(Acc(self.n) and self.n == 0)

    def over(self, k: int) -> bool:
        Ensures(Result() == (k > 10))
        return k > Config.limit

    def stepped(self, k: int) -> int:
        Ensures(Result() == k + 2)
        return k + self.step


def client() -> None:
    c = Config()
    assert Config.limit == 10
    assert Config.step + Config.plain + Config.top == 10
    assert not c.over(3)
    assert c.stepped(1) == 3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert Config.limit == 11
