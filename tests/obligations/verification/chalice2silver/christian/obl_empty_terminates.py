# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/christian/obl_empty_terminates.chalice`` test from
Chalice2Silver test suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Requires,
)
from nagini_contracts.obligations import *


class A:

    def __init__(self, x: 'A', y: int) -> None:
        self.x = x
        self.y = y

    def t(self) -> None:
        Requires(Acc(self.y) and MustTerminate(self.y))

    def t2(self) -> None:
        Requires(Acc(self.y) and MustTerminate(self.y))
        Assert(self.y > 0)
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(False)

    def mr(self) -> None:
        Requires(MustTerminate(1))
