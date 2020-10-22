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



def thread2(l: CellLock, c: Cell, secret: int) -> None:
    Requires(Low(l) and l.get_locked() is c)
    Requires(LowEvent())
    Requires(TerminatesSif(True, 2))
    while secret > 0:
        Invariant(TerminatesSif(True, secret))
        secret -= 1
    l.acquire()
    c.leak = False
    l.release()
