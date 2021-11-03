# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock
from nagini_contracts.obligations import WaitLevel, Level

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
    Requires(LowEvent() and WaitLevel() < Level(l))
    while secret > 0:
        # When writing TerminatesSif(e1, e2) as the last part of the invariant, Nagini does not check that the
        # termination condition is low (which is the default), but instead checks that the loop terminates if e1 holds
        # initially, using the ranking function e2. This is an alternative sufficient condition.
        Invariant(TerminatesSif(True, secret))
        secret -= 1
    l.acquire()
    c.leak = False
    l.release()
