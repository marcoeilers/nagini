# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from nagini_contracts.obligations import Level, WaitLevel, MustTerminate


class Cell:
    def __init__(self, val: int) -> None:
        self.value = val
        Ensures(Acc(self.value) and self.value == val)


class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().value)


class CellMonitor:
    def __init__(self) -> None:
        self.c = Cell(12)
        self.c.value = 14
        self.l = CellLock(self.c)
        #:: ExpectedOutput(assignment.failed:insufficient.permission)
        self.c.value = 16
        Ensures(Acc(self.c) and Acc(self.l) and self.l.get_locked() is self.c)
        Ensures(WaitLevel() < Level(self.l))

    def acquire_release_correct(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)
        self.l.acquire()
        self.c.value += 2
        self.l.release()

    def unspecified_locked_object(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2))
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        self.l.acquire()
        #:: ExpectedOutput(assignment.failed:insufficient.permission)
        self.c.value += 2
        self.l.release()

    def unspecified_waitlevel(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.l.acquire()
        self.c.value += 2
        self.l.release()

    #:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
    def no_release(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        self.l.acquire()
        self.c.value += 2

    def release_fails_permission(self) -> None:
        Requires(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        self.l.acquire()
        self.c.value += 2
        leak_permission(self.c)
        #:: ExpectedOutput(lock.invariant.not.established:insufficient.permission)
        self.l.release()


def leak_permission(c: Cell) -> None:
    Requires(Acc(c.value))
    Requires(MustTerminate(1))
    pass


def client_1() -> None:
    twc = CellMonitor()
    twc.l.acquire()
    twc.l.release()
    twc.acquire_release_correct()


def client_2() -> None:
    twc = CellMonitor()
    twc.acquire_release_correct()


class NCell:
    def __init__(self, val: int) -> None:
        Ensures(Acc(self.n) and self.n == val)
        self.n = val  # type: int


class NCellLock(Lock[NCell]):
    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().n) and self.get_locked().n >= 0


def ncell_correct(c: NCell, l: NCellLock) -> None:
    Requires(l.get_locked() is c)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    c.n += 12
    l.release()


def release_fails_assertion(c: NCell, l: NCellLock) -> None:
    Requires(l.get_locked() is c)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    c.n -= 2
    #:: ExpectedOutput(lock.invariant.not.established:assertion.false)
    l.release()


def ncell_client_correct() -> None:
    c = NCell(3)
    l = NCellLock(c)
    l.acquire()
    assert c.n >= 0
    l.release()
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def ncell_share_invariant_fail() -> None:
    c = NCell(-3)
    #:: ExpectedOutput(lock.invariant.not.established:assertion.false)
    l = NCellLock(c)


def ncell_share_permission_lost() -> None:
    c = NCell(3)
    l = NCellLock(c)
    #:: ExpectedOutput(assert.failed:insufficient.permission)
    assert c.n >= 0


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def ncell_share_havoc() -> None:
    c = NCell(3)
    assert c.n == 3
    l = NCellLock(c)
    l.acquire()
    assert c.n >= 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c.n == 3
