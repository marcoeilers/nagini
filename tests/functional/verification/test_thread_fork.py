# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread, MayStart, getArg, getMethod, Joinable, ThreadPost, getOld, arg
from nagini_contracts.obligations import MustTerminate, WaitLevel, Level


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)

    def incr(self, n: int) -> None:
        Requires(Acc(self.val))
        Ensures(Acc(self.val) and self.val == Old(self.val) + n)
        self.val = self.val + n


def decr(c: Cell, n: int) -> int:
    Requires(Acc(c.val))
    Requires(MustTerminate(2))
    Ensures(Acc(c.val) and c.val == Old(c.val) - n)
    c.val = c.val - n
    return c.val


def client_fork(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == Cell.incr)
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    Ensures(getOld(t, arg(0).val) == 12)
    Ensures(WaitLevel() < Level(t))
    #:: ExpectedOutput(postcondition.violated:insufficient.permission)
    Ensures(Acc(MayStart(t)))
    cell.val = 12
    t.start(decr, Cell.incr)


def client_fork_missing_start_perm(t: Thread, b: bool, cell: Cell) -> None:
    Requires(getMethod(t) == Cell.incr)
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    #:: ExpectedOutput(thread.start.failed:missing.start.permission)
    t.start(decr, Cell.incr)


def client_fork_method_unknown(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    #:: ExpectedOutput(thread.start.failed:method.not.listed)
    t.start(decr, Cell.incr)


def client_fork_precond_not_fulfilled(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == Cell.incr)
    Requires(cell is getArg(t, 0))
    #:: ExpectedOutput(thread.start.failed:insufficient.permission)
    t.start(decr, Cell.incr)


def client_fork_wrong_old_1(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == Cell.incr)
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(getOld(t, arg(0).val.val) == 12)
    cell.val = 12
    t.start(decr, Cell.incr)


def client_fork_wrong_old_2(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == Cell.incr)
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(getOld(t, arg(0).val) == 14)
    cell.val = 12
    t.start(decr, Cell.incr)


def client_fork_join_perms(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == decr)
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    Ensures(Joinable(t))
    Ensures(Acc(ThreadPost(t)))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    t.start(decr, Cell.incr)


def client_fork_wrong_mayjoin(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == Cell.incr)
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Joinable(t))
    t.start(decr, Cell.incr)


def client_fork_wrong_thread_post(t: Thread, b: bool, cell: Cell) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == Cell.incr)
    Requires(Acc(cell.val))
    Requires(cell is getArg(t, 0))
    #:: ExpectedOutput(postcondition.violated:insufficient.permission)
    Ensures(Acc(ThreadPost(t)))
    t.start(decr, Cell.incr)