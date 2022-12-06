# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock
from nagini_contracts.obligations import WaitLevel, Level


class Cell:
    def __init__(self, val: int) -> None:
        Requires(TerminatesSif(True, 2))
        self.value = val
        Ensures(Acc(self.value) and self.value == val)


class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().value) and Low(self.get_locked().value)

def thread1(l: CellLock, c: Cell, secret: int) -> None:
    Requires(Low(l) and l.get_locked() is c)
    Requires(LowEvent() and WaitLevel() < Level(l))
    for i in range(0, 5):
        Invariant(WaitLevel() < Level(l))
        Invariant(Low(i) and Low(Previous(i)))
        l.acquire()
        c.value = i
        l.release()


def thread2(l: CellLock, c: Cell) -> int:
    Requires(Low(l) and l.get_locked() is c)
    Requires(LowEvent() and WaitLevel() < Level(l))
    Ensures(Low(Result()))
    for i in range(0, 2):
        Invariant(Low(i) and Low(Previous(i)))
        pass
    l.acquire()
    c.value = 1
    l.release()
    for i in range(0, 2):
        Invariant(Low(i) and Low(Previous(i)))
        pass
    l.acquire()
    res = c.value
    l.release()
    return res