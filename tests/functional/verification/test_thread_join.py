from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread, MayStart, getArg, getMethod, MayJoin, ThreadPost, getOld, arg
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


def thread_join(t: Thread, cl: Cell) -> None:
    Requires(getMethod(t) == decr)
    Requires(getArg(t, 0) is cl)
    Requires(getArg(t, 1) is 7)
    Requires(getOld(t, arg(0).val) is 123)
    Requires(Acc(ThreadPost(t)))
    Requires(WaitLevel() < Level(t))
    Ensures(MayJoin(t))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    t.join(Cell.incr, decr)
    assert cl.val == 116
    cl.val = 11


def thread_join_wrong_level(t: Thread, cl: Cell) -> None:
    Requires(getMethod(t) == decr)
    Requires(getArg(t, 0) is cl)
    Requires(getArg(t, 1) is 7)
    Requires(getOld(t, arg(0).val) is 123)
    Requires(Acc(ThreadPost(t)))
    #:: ExpectedOutput(thread.join.failed:wait.level.invalid)
    t.join(Cell.incr, decr)


def thread_join_wrong_method(t: Thread, cl: Cell) -> None:
    Requires(getMethod(t) == Cell.incr)
    Requires(getArg(t, 0) is cl)
    Requires(getArg(t, 1) is 7)
    Requires(getOld(t, arg(0).val) is 123)
    Requires(Acc(ThreadPost(t)))
    Requires(WaitLevel() < Level(t))
    t.join(decr)
    #:: ExpectedOutput(assert.failed:insufficient.permission)|ExpectedOutput(carbon)(application.precondition:assertion.false)
    assert cl.val == 116


def thread_join_minimal(t: Thread, cl: Cell) -> None:
    Requires(MayJoin(t))
    Requires(WaitLevel() < Level(t))
    t.join(Cell.incr, decr)
    #:: ExpectedOutput(assert.failed:insufficient.permission)|ExpectedOutput(carbon)(application.precondition:assertion.false)
    assert cl.val == 116


def thread_join_no_post_perm(t: Thread, cl: Cell) -> None:
    Requires(getMethod(t) == decr)
    Requires(getArg(t, 0) is cl)
    Requires(getArg(t, 1) is 7)
    Requires(getOld(t, arg(0).val) is 123)
    Requires(MayJoin(t))
    Requires(WaitLevel() < Level(t))
    t.join(Cell.incr, decr)
    #:: ExpectedOutput(assert.failed:insufficient.permission)|ExpectedOutput(carbon)(application.precondition:assertion.false)
    assert cl.val == 116


def thread_join_part_perm(t: Thread, cl: Cell) -> None:
    Requires(getMethod(t) == decr)
    Requires(getArg(t, 0) is cl)
    Requires(getArg(t, 1) is 7)
    Requires(getOld(t, arg(0).val) is 123)
    Requires(Acc(ThreadPost(t), 1/2))
    Requires(WaitLevel() < Level(t))
    t.join(Cell.incr, decr)
    assert cl.val == 116
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    cl.val = 11


def thread_join_not_joinable(t: Thread, cl: Cell) -> None:
    Requires(getMethod(t) == decr)
    Requires(getArg(t, 0) is cl)
    Requires(getArg(t, 1) is 7)
    Requires(getOld(t, arg(0).val) is 123)
    Requires(WaitLevel() < Level(t))
    #:: ExpectedOutput(thread.join.failed:thread.not.joinable)
    t.join(Cell.incr, decr)
