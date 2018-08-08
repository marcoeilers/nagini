from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock
from nagini_contracts.thread import (
    Thread, MayStart, getArg, getMethod, Joinable, ThreadPost, getOld, arg
)
from nagini_contracts.obligations import MustTerminate, WaitLevel, Level


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)

#     def incr(self, n: int) -> None:
#         Requires(Acc(self.val))
#         Ensures(Acc(self.val) and self.val == Old(self.val) + n)
#         self.val = self.val + n

class CellLock(Lock[Cell]):
    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().val) and LowVal(self.get_locked().val)

# def decr(c: Cell, n: int) -> int:
#     Requires(Acc(c.val))
#     Requires(MustTerminate(2))
#     Ensures(Acc(c.val) and c.val == Old(c.val) - n)
#     c.val = c.val - n
#     return c.val

def sif_print(x: int) -> None:
    Requires(LowEvent())
    Requires(LowVal(x))
    Requires(MustTerminate(1))
    pass

def printTwice(l: Lock[Cell], x: int) -> None:
    Requires(LowEvent())
    Requires(Low(l) and Low(x))
    Requires(MustTerminate(4))
    Requires(WaitLevel() < Level(l))
    l.acquire()
    sif_print(x)
    sif_print(x)
    l.release()

def client(secret: bool) -> None:
    c1 = Cell()
    l1 = CellLock(c1)
    c2 = Cell()
    l2 = CellLock(c2)
    if secret:
        x = l1
    else:
        x = l2
    t1 = Thread(target=printTwice, args=(x, 1)) # x aliases l2 depending on secret
    t2 = Thread(target=printTwice, args=(l2, 2))
    #:: ExpectedOutput(thread.start.failed:assertion.false)
    t1.start(printTwice)
    t2.start(printTwice)
    # if x == l2 outputs can only be 1122 or 2211, otherwise e.g. 1212 is possible.
