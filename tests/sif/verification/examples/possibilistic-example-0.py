from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock

class Cell:
    def __init__(self) -> None:
        Requires(TerminatesSif(True, 2))
        self.go_1 = False
        self.go_2 = False
        self.leak = False

class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return (Acc(self.get_locked().go_1) and
                Acc(self.get_locked().go_2) and
                Acc(self.get_locked().leak) and Low(self.get_locked().leak))


def thread_0(l: CellLock, c: Cell, secret: bool) -> bool:
    Requires(Low(l) and l.get_locked() is c)
    Requires(LowEvent())
    Requires(TerminatesSif(True, 2))
    Ensures(Low(Result()))
    l.acquire()
    if secret:
        c.go_1 = True
    else:
        c.go_2 = True
    l.release()
    l.acquire()
    leak = c.leak
    l.release()
    return leak


def thread1(l: CellLock, c: Cell, secret: int) -> None:
    Requires(Low(l) and l.get_locked() is c)
    Requires(TerminatesSif(True, 2))
    l.acquire()
    go = c.go_1
    l.release()
    while not go:
        Invariant(TerminatesSif(not go, 1))
        pass
    l.acquire()
    c.leak = True
    l.release()


def thread2(l: CellLock, c: Cell, secret: int) -> None:
    Requires(Low(l) and l.get_locked() is c)
    Requires(TerminatesSif(True, 2))
    l.acquire()
    go = c.go_2
    l.release()
    while not go:
        Invariant(TerminatesSif(not go, 1))
        pass
    l.acquire()
    c.leak = False
    l.release()
