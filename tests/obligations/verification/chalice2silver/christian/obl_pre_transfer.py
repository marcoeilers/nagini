"""
This test is a ported version of
``obligations/christian/obl_pre_transfer.chalice`` test from
Chalice2Silver test suite.
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

    def unbounded_transfer(self) -> None:
        r = Lock(self)
        r.acquire()
        self.does_release(r)

    def does_release(self, r: Lock['A']) -> None:
        Requires(MustRelease(r, 2))
        Requires(r.invariant())
        r.release()

    def quick_release(self, r: Lock['A']) -> None:
        Requires(MustTerminate(2) and MustRelease(r, 2))
        Requires(r.invariant())
        r.release()

    def diverge(self, r: Lock['A']) -> None:
        Requires(r is not None)

    def unbounded_transfer_diverge(self) -> None:
        r = Lock(self)
        r.acquire()

        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
        self.diverge(r)

        r.release()

    def skip(self, r: Lock[A]) -> None:
        Requires(MustTerminate(1))

    def unbounded_skip(self) -> None:
        r = Lock(self)
        r.acquire()
        self.skip(r)
        r.release()

    def unbounded_skip_with_mustTerminate(self) -> None:
        Requires(MustTerminate(3))
        r = Lock(self)
        r.acquire()
        self.skip(r)
        self.quick_release(r)

    def mustTerminate_still_applies(self) -> None:
        Requires(MustTerminate(3))
        Requires(MustTerminate(3))
        r = Lock(self)
        r.acquire()
        self.skip(r)
        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
        self.does_release(r)
