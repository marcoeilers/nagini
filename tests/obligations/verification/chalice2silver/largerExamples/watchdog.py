# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/largerExamples/watchdog.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Fold,
    Implies,
    Invariant,
    Predicate,
    Requires,
    Unfold
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock
from nagini_contracts.thread import Thread


class Data:
    def __init__(self) -> None:
        self.d = 0
        self.lock = DataLock(self)
        Ensures(Acc(self.lock) and
                WaitLevel() < Level(self.lock) and
                self.lock.get_locked() is self)


class DataLock(Lock[Data]):
    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().d) and self.get_locked().d % 2 == 0


class WatchDog:

    def __init__(self) -> None:
        self.running = False
        Ensures(Acc(self.running))

    def delay(self, t: int) -> None:
        Requires(MustTerminate(t))

    def watch(self, d: Data) -> None:
        Requires(Acc(self.running))
        Requires(Acc(d.lock, 1/2) and d.lock.get_locked() is d)
        Requires(WaitLevel() < Level(d.lock))  # guarantees deadlock freedom
        self.running = True
        d.lock.acquire()
        while (self.running):
            Invariant(Acc(self.running))
            Invariant(Acc(d.lock, 1/2) and d.lock.get_locked() is d)
            Invariant(MustRelease(d.lock, 1))
            Invariant(WaitLevel() < Level(d.lock))  # guarantees deadlock freedom
            Invariant(Acc(d.d) and d.d % 2 == 0)
            # We can check that the invariant holds.
            assert d.d % 2 == 0
            d.lock.release()
            # Others may acquire the lock and modify d
            self.delay(5)
            d.lock.acquire()
        d.lock.release()


def main() -> None:
    data = Data()
    w = WatchDog()
    wthread = Thread(None, w.watch, None, (data,))
    # Spawn the watchdog thread
    wthread.start(w.watch)
    data.lock.acquire()
    data.d = 0
    while True:
        Invariant(Acc(data.lock, 1/4))
        Invariant(data.lock.get_locked() is data)
        Invariant(WaitLevel() < Level(data.lock))  # guarantees deadlock freedom
        Invariant(MustRelease(data.lock, 1))
        Invariant(Acc(data.d) and data.d % 2 == 0)

        # Modify the locked data in a legal way
        data.d = data.d + 2

        data.lock.release()
        # Others may acquire the lock
        data.lock.acquire()

