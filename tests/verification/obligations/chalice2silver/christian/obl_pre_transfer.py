"""
This test is a ported version of
``obligations/christian/obl_pre_transfer.chalice`` test from
Chalice2Silver test suite.
"""


from threading import Lock

from py2viper_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Invariant,
    Implies,
    Requires,
)
from py2viper_contracts.obligations import *


class A:

    def __init__(self) -> None:
        self.x = None   # type: Lock
        self.y = 0

    def unbounded_transfer(self) -> None:
        r = Lock()
        r.acquire()
        self.does_release(r)

    def does_release(self, r: Lock) -> None:
        Requires(MustRelease(r, 2))
        r.release()

    def quick_release(self, r: Lock) -> None:
        Requires(MustTerminate(2) and MustRelease(r, 2))
        r.release()

    def diverge(self, r: Lock) -> None:
        Requires(r is not None)

    def unbounded_transfer_diverge(self) -> None:
        r = Lock()
        r.acquire()

        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
        self.diverge(r)

        r.release()

    def skip(self, r: Lock) -> None:
        Requires(MustTerminate(1))

    def unbounded_skip(self) -> None:
        r = Lock()
        r.acquire()
        self.skip(r)
        r.release()

    def unbounded_skip_with_mustTerminate(self) -> None:
        Requires(MustTerminate(3))
        r = Lock()
        r.acquire()
        self.skip(r)
        self.quick_release(r)

    def mustTerminate_still_applies(self) -> None:
        Requires(MustTerminate(3))
        r = Lock()
        r.acquire()
        self.skip(r)
        #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
        self.does_release(r)
