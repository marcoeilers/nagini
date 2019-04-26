# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    Assert,
    Requires,
    Ensures
)
from typing import Optional


class B:
    pass


class C:
    pass


class A:

    def __init__(self) -> None:
        self.b = None   # type: Optional[B]
        self.c = None   # type: Optional[C]

    def test(self) -> None:
        Requires(Acc(self.b) and Acc(self.c))
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(self.b is not self.c)


class A2:

    def __init__(self) -> None:
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Acc(self.b))
        Ensures(Acc(self.c))
        self.b = None   # type: B
        self.c = None   # type: C

    def test(self) -> None:
        Requires(Acc(self.b) and Acc(self.c))
        Assert(self.b is not self.c)
