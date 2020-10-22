from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock

class Cell:
    def __init__(self, val: int) -> None:
        Requires(TerminatesSif(True, 2))
        self.value = val
        Ensures(Acc(self.value) and self.value == val)


class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().value) and LowVal(self.get_locked().value)


def thread1(l: CellLock, c: Cell) -> None:
    Requires(Low(l) and l.get_locked() is c)
    Requires(LowEvent())
    Requires(TerminatesSif(True, 2))
    ctr = 0
    while ctr < 100:
        Invariant(Low(ctr))
        Invariant(TerminatesSif(True, 100-ctr))
        ctr += 1
    l.acquire()
    c.value = 1
    l.release()


def thread2(l: CellLock, c: Cell, secret: int) -> None:
    Requires(Low(l) and l.get_locked() is c)
    Requires(LowEvent())
    Requires(TerminatesSif(True, 2))
    ctr = 0
    while ctr < secret:
        Invariant(TerminatesSif(True, secret - ctr if secret > 0 else 1))
        ctr += 1
    l.acquire()
    c.value = 2
    l.release()
