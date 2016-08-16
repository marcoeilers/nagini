"""
This test is a ported version of
``obligations/largerExamples/watchdog.chalice`` test from Chalice2Silver
test suite.
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


class WatchDog:

    def __init__(self) -> None:
        self.running = False

    def delay(self, t: int) -> None:
        Requires(MustTerminate(t))

    def watch(self, d: Lock) -> None:
        Requires(d is not None)
        Requires(Acc(self.running))
        self.running = True     # TODO: self.running should be in Lock
                                # invariant.
        d.acquire()
        while (self.running):
            Invariant(Acc(self.running))
            Invariant(MustRelease(d, 1))
            # TODO: Check some property here.
            d.release()
            self.delay(5)
            d.acquire()
        d.release()


def main() -> None:
    # TODO: Encode this method. (Need to support fork statement for
    # that.)
    pass
