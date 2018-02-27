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

    def acquire_release_correct(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)
        self.l.acquire()
        Unfold(self.l.invariant())
        self.c.value += 2
        Fold(self.l.invariant())
        self.l.release()

    def fold_missing(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        self.l.acquire()
        Unfold(self.l.invariant())
        self.c.value += 2
        #:: ExpectedOutput(call.precondition:insufficient.permission)
        self.l.release()

    def unspecified_locked_object(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2))
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        self.l.acquire()
        Unfold(self.l.invariant())
        #:: ExpectedOutput(assignment.failed:insufficient.permission)|ExpectedOutput(carbon)(application.precondition:assertion.false)
        self.c.value += 2
        Fold(self.l.invariant())
        self.l.release()

    def unspecified_waitlevel(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.l.acquire()
        Unfold(self.l.invariant())
        self.c.value += 2
        Fold(self.l.invariant())
        self.l.release()

    #:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
    def no_release(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        self.l.acquire()
        Unfold(self.l.invariant())
        self.c.value += 2
        Fold(self.l.invariant())

    def no_acquire(self) -> None:
        Requires(Acc(self.l, 1/2) and Acc(self.c, 1/2) and self.l.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.l))
        Ensures(Acc(self.l, 1 / 2) and Acc(self.c, 1 / 2))
        #:: ExpectedOutput(unfold.failed:insufficient.permission)
        Unfold(self.l.invariant())
        self.c.value += 2
        Fold(self.l.invariant())
        self.l.release()


def client_1() -> None:
    twc = ThingWithCell()
    twc.l.acquire()
    twc.l.release()
    twc.acquire_release_correct()


def client_2() -> None:
    twc = ThingWithCell()
    twc.acquire_release_correct()


class NCell:
    def __init__(self, val: int) -> None:
        Ensures(Acc(self.n) and self.n == 0)
        self.n = 0  # type: int


class NCellLock(Lock[NCell]):
    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().n) and self.get_locked().n >= 0