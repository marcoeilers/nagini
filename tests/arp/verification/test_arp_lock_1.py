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
        return Acc(self.get_locked().value)


class ThingWithCell:
    def __init__(self) -> None:
        self.c = Cell(12)
        self.c.value = 14
        self.l = CellLock(self.c)
        #:: ExpectedOutput(assignment.failed:insufficient.permission)
        self.c.value = 16
        Ensures(Acc(self.c) and Acc(self.l) and self.l.get_locked() is self.c)
        Ensures(WaitLevel() < Level(self.l))

    def do_a_thing(self) -> None:
        Requires(Rd(self.l) and Rd(self.c) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Rd(self.l) and Rd(self.c))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)
        self.l.acquire()
        self.c.value += 2
        self.l.release()

    def do_a_thing_3(self) -> None:
        Requires(Rd(self.l) and Rd(self.c))
        Requires(WaitLevel() < Level(self.l))
        Ensures(Rd(self.l) and Rd(self.c))
        self.l.acquire()
        #:: ExpectedOutput(assignment.failed:insufficient.permission)
        self.c.value += 2
        self.l.release()

    def do_a_thing_4(self) -> None:
        Requires(Rd(self.l) and Rd(self.c) and self.l.get_locked() is self.c)
        Ensures(Rd(self.l) and Rd(self.c))
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.l.acquire()
        self.c.value += 2
        self.l.release()

    #:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
    def do_a_thing_5(self) -> None:
        Requires(Rd(self.l) and Rd(self.c) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Rd(self.l) and Rd(self.c))
        self.l.acquire()
        self.c.value += 2

    def do_a_thing_6(self) -> None:
        Requires(Rd(self.l) and Rd(self.c) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Rd(self.l) and Rd(self.c))
        #:: ExpectedOutput(assignment.failed:insufficient.permission)
        self.c.value += 2
        self.l.release()


def client_1() -> None:
    twc = ThingWithCell()
    twc.l.acquire()
    twc.l.release()
    twc.do_a_thing()


def client_2() -> None:
    twc = ThingWithCell()
    twc.do_a_thing()