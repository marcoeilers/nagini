# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/largerExamples/watchdog.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Ensures,
    Invariant,
    Predicate,
    Requires,
    Fold,
    Unfold,
    ContractOnly
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock
from nagini_contracts.thread import Thread

@ContractOnly
def printInt(i: int) -> None:
    Requires(MustTerminate(1))
    pass


class Data:
    def __init__(self) -> None:
        self.d = 0
        Fold(DataInv(self))
        Ensures(DataInv(self))


@Predicate
def prewatch(wd: 'WatchDog') -> bool:
    return Acc(wd.running)

@Predicate
def DataInv(d: Data) -> bool:
    return Acc(d.d) and d.d % 2 == 0


class DataLock(Lock[Data]):
    @Predicate
    def invariant(self) -> bool:
        return DataInv(self.get_locked())


class WatchDog:

    def __init__(self) -> None:
        self.running = False
        Ensures(Acc(self.running))

    def delay(self, t: int) -> None:
        Requires(MustTerminate(t))

    def watch(self, d: Data, dlck: DataLock) -> None:
        Requires(prewatch(self))
        Requires(dlck.get_locked() is d)
        Requires(WaitLevel() < Level(dlck))  # guarantees deadlock freedom
        Unfold(prewatch(self))
        self.running = True
        dlck.acquire()
        Unfold(DataInv(d))
        while (self.running):
            Invariant(Acc(self.running))
            Invariant(dlck.get_locked() is d)
            Invariant(MustRelease(dlck, 1))
            Invariant(WaitLevel() < Level(dlck))  # guarantees deadlock freedom
            Invariant(Acc(d.d) and d.d % 2 == 0)
            # We can check that the invariant holds.
            assert d.d % 2 == 0
            printInt(d.d)
            Fold(DataInv(d))
            dlck.release()
            # Others may acquire the lock and modify d
            self.delay(5)
            dlck.acquire()
            Unfold(DataInv(d))
        Fold(DataInv(d))
        dlck.release()


def main() -> None:
    data = Data()
    dlck = DataLock(data)
    w = WatchDog()
    wthread = Thread(None, w.watch, None, (data,dlck))
    Fold(prewatch(w))
    # Spawn the watchdog thread
    wthread.start(w.watch)
    dlck.acquire()
    Unfold(DataInv(data))
    data.d = 0
    while True:
        Invariant(dlck.get_locked() is data)
        Invariant(WaitLevel() < Level(dlck))  # guarantees deadlock freedom
        Invariant(MustRelease(dlck, 1))
        Invariant(Acc(data.d) and data.d % 2 == 0)

        # Modify the locked data in a legal way
        data.d = data.d + 2

        Fold(DataInv(data))
        dlck.release()
        # Others may acquire the lock
        dlck.acquire()
        Unfold(DataInv(data))

