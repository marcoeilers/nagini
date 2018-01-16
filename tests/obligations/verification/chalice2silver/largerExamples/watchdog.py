"""
This test is a ported version of
``obligations/largerExamples/watchdog.chalice`` test from Chalice2Silver
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


class WatchDog:

    def __init__(self) -> None:
        self.running = False

    def delay(self, t: int) -> None:
        Requires(MustTerminate(t))

    def watch(self, d: Lock['WatchDog']) -> None:
        Requires(d is not None)
        Requires(Acc(self.running))
        Requires(WaitLevel() < Level(d))
        self.running = True     # TODO: self.running should be in Lock
                                # invariant.
        d.acquire()
        while (self.running):
            Invariant(Acc(self.running))
            Invariant(MustRelease(d, 1))
            Invariant(WaitLevel() < Level(d))
            Invariant(d.invariant())
            # TODO: Check some property here.
            d.release()
            self.delay(5)
            d.acquire()
        d.release()


def main() -> None:
    # TODO: Encode this method. (Need to support fork statement for
    # that.)
    pass
