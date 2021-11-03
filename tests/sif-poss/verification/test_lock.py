# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from nagini_contracts.obligations import Level, WaitLevel


class Cell:
    def __init__(self, val: int) -> None:
        self.value = val
        Ensures(Acc(self.value) and self.value == val)


class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().value) and LowVal(self.get_locked().value)

def client(secret: bool) -> None:
    Requires(LowEvent())
    c = Cell(1)
    l = CellLock(c)
    l.acquire()
    c.value = 4
    if secret:
        #:: ExpectedOutput(call.precondition:assertion.false)
        l.release()
        l.acquire()
    c.value = 5
    l.release()

