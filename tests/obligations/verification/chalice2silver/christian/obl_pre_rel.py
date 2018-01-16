"""
This test is a ported version of
``obligations/christian/obl_pre_rel.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Implies,
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock
from typing import Optional


class A:

    def __init__(self) -> None:
        self.x = None   # type: Optional[Lock[A]]
        self.y = 0

    def t(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        Requires(self.x.invariant())
        Ensures(Acc(self.x))
        self.x.release()

    def mr(self, other: 'A') -> None:
        Requires(Acc(other.x) and MustRelease(other.x, 2))
        Requires(other.x.invariant())
        Ensures(Acc(other.x))
        other.x.release()

    #:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
    def mnor(self, other: 'A') -> None:
        Requires(Acc(other.x) and MustRelease(other.x, 2))
        Ensures(Acc(other.x))
        other.x = None
