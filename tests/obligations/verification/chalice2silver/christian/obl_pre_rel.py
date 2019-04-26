# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

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
    Predicate,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock
from typing import Optional


class ObjectLock(Lock['A']):
    @Predicate
    def invariant(self) -> bool:
        return True

class A:

    def __init__(self) -> None:
        self.x = None   # type: Optional[ObjectLock]
        self.y = 0

    def t(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        Ensures(Acc(self.x))
        self.x.release()

    def mr(self, other: 'A') -> None:
        Requires(Acc(other.x) and MustRelease(other.x, 2))
        Ensures(Acc(other.x))
        other.x.release()

    #:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
    def mnor(self, other: 'A') -> None:
        Requires(Acc(other.x) and MustRelease(other.x, 2))
        Ensures(Acc(other.x))
        other.x = None