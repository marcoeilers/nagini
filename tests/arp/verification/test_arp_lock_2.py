# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from nagini_contracts.obligations import Level, WaitLevel, MustTerminate
from nagini_contracts.thread import Thread


class Cell:
    def __init__(self, val: int) -> None:
        self.value = val
        self.n = 0  # type: int
        Ensures(Acc(self.value) and self.value == val)
        Ensures(Acc(self.n) and self.n == 0)


class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().n) and self.get_locked().n >= 0 and \
               Acc(self.get_locked().value, 1 - self.get_locked().n * ARP())


class ThingWithCell:
    def __init__(self) -> None:
        self.c = Cell(12)
        self.c.value = 14
        self.l = CellLock(self.c)
        Ensures(Acc(self.c) and Acc(self.l) and self.l.get_locked() is self.c)
        Ensures(WaitLevel() < Level(self.l))

    def need_value(self) -> None:
        Requires(Rd(self.c) and Rd(self.c.value))
        Requires(MustTerminate(2))
        Ensures(Rd(self.c) and Rd(self.c.value))
        pass

    def do_a_thing(self) -> None:
        Requires(Rd(self.l) and Rd(self.c) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Rd(self.l) and Rd(self.c))
        #:: ExpectedOutput(postcondition.violated:assertion.false)|MissingOutput(postcondition.violated:assertion.false, 320)
        Ensures(False)
        self.l.acquire()
        self.c.n += 1
        #:: UnexpectedOutput(silicon)(lock.invariant.not.established:assertion.false, 320)
        self.l.release()
        self.need_value()
        t1 = Thread(None, self.need_value, args=())
        t2 = Thread(None, self.need_value, args=())
        t1.start(self.need_value)
        t2.start(self.need_value)
        t1.join(self.need_value)
        t2.join(self.need_value)
        #:: ExpectedOutput(carbon)(assert.failed:assertion.false)
        Assert(False)  # Carbon does not terminate for the next statement
        self.need_value()
        self.l.acquire()
        self.c.n -= 1
        self.l.release()


def client_1() -> None:
    twc = ThingWithCell()
    twc.l.acquire()
    twc.l.release()
    twc.do_a_thing()


def client_2() -> None:
    twc = ThingWithCell()
    twc.do_a_thing()
