# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

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

class CellLock(Lock[Cell]):
    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().val) and LowVal(self.get_locked().val)

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

def printZero() -> None:
    Requires(LowEvent())
    sif_print(0)

def printOne() -> None:
    Requires(LowEvent())
    sif_print(1)

def zero(c: Cell) -> None:
    Requires(MustTerminate(1))
    Requires(Acc(c.val))
    Ensures(Acc(c.val))
    Ensures(Low(c.val))
    c.val = 0

def one(c: Cell) -> None:
    Requires(MustTerminate(1))
    Requires(Acc(c.val))
    Ensures(Acc(c.val))
    Ensures(Low(c.val))
    c.val = 1

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

def fork_lowevent(secret: bool) -> None:
    if secret:
        t = Thread(target=printZero, args=())
    else:
        t = Thread(target=printOne, args=())
    #:: ExpectedOutput(thread.start.failed:assertion.false)
    t.start(printZero, printOne)

def join_low(secret: bool) -> None:
    c = Cell()
    if secret:
        t = Thread(target=zero, args=(c,))
    else:
        t = Thread(target=one, args=(c,))
    t.start(zero, one)
    t.join(zero, one)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Low(c.val))

class A:
    def foo(self) -> int:
        Ensures(Low(Result()))
        return 0

class B(A):
    def foo(self) -> int:
        Ensures(Low(Result()))
        return 1

def join_low_dyn_bound(secret: bool) -> None:
    if secret:
        x = A()
    else:
        x = B()
    t = Thread(target=x.foo, args=())
    t.start(x.foo)
    #:: ExpectedOutput(thread.join.failed:thread.not.joinable)
    t.join(x.foo)
