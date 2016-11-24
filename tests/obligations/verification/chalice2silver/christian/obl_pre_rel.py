"""
This test is a ported version of
``obligations/christian/obl_pre_rel.chalice`` test from Chalice2Silver
test suite.
"""


from py2viper_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Implies,
    Invariant,
    Requires,
)
from py2viper_contracts.obligations import *
from py2viper_contracts.lock import Lock
from typing import Optional


class A:

    def __init__(self) -> None:
        self.x = None   # type: Optional[Lock]
        self.y = 0

    def t(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        Ensures(Acc(self.x))
        self.x.release()

    def mr(self, other: A) -> None:
        Requires(Acc(other.x) and MustRelease(other.x, 2))
        Ensures(Acc(other.x))
        other.x.release()

    #:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
    def mnor(self, other: A) -> None:
        Requires(Acc(other.x) and MustRelease(other.x, 2))
        Ensures(Acc(other.x))
        other.x = None
