# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock
from nagini_contracts.obligations import WaitLevel, Level, MustRelease

class Cell:
    def __init__(self) -> None:
        self.go_1 = False
        self.go_2 = False
        self.leak = False
        self.proceed = False

class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return (Acc(self.get_locked().go_1) and
                Acc(self.get_locked().go_2) and
                Acc(self.get_locked().proceed) and Low(self.get_locked().proceed) and
                Acc(self.get_locked().leak) and Low(self.get_locked().leak))


def thread_0(l: CellLock, c: Cell, secret: bool) -> bool:
    Requires(Low(l) and l.get_locked() is c)
    Requires(LowEvent())
    Ensures(Low(Result()))
    l.acquire()
    if secret:
        c.go_1 = True
    else:
        c.go_2 = True
    l.release()
    l.acquire()
    Fold(l.invariant())
    while not Unfolding(l.invariant(), c.proceed):
        Invariant(l.invariant() and MustRelease(l))
        Unfold(l.invariant())
        l.release()
        l.acquire()
        Fold(l.invariant())
    Unfold(l.invariant())
    leak = c.leak
    l.release()
    return leak


def thread1(l: CellLock, c: Cell, secret: int) -> None:
    Requires(Low(l) and l.get_locked() is c)
    l.acquire()
    #:: ExpectedOutput(possibilistic.sif.violated:high.branch)
    while not c.go_1:
        l.release()
        l.acquire()
    c.leak = True
    c.proceed = True
    l.release()


def thread2(l: CellLock, c: Cell, secret: int) -> None:
    Requires(Low(l) and l.get_locked() is c)
    l.acquire()
    #:: ExpectedOutput(possibilistic.sif.violated:high.branch)
    while not c.go_2:
        l.release()
        l.acquire()
    c.leak = False
    c.proceed = True
    l.release()
