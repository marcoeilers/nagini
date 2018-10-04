from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread, MayStart, getArg, getMethod
from nagini_contracts.obligations import MustTerminate


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


def client_create(b: bool) -> Thread:
    Ensures(MayStart(Result()))
    Ensures(Implies(b, getArg(Result(), 1) is 3))
    Ensures(Implies(not b, getArg(Result(), 1) is 6))
    Ensures(Implies(not b, getMethod(Result()) == decr))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(getArg(Result(), 2) is None)
    cl = Cell()
    if b:
        t = Thread(None, target=cl.incr, args=(3,))
    else:
        t = Thread(target=decr, group=None, args=(cl, 6))
    return t

def client_create_group_not_none() -> Thread:
    cl = Cell()
    #:: ExpectedOutput(thread.creation.failed:assertion.false)
    t = Thread(object(), target=cl.incr, args=(3,))
    return t


def client_create_wrong_arg(b: bool) -> Thread:
    cl = Cell()
    if b:
        t = Thread(None, cl.incr, 'some_name', (3,))
    else:
        #:: ExpectedOutput(thread.creation.failed:invalid.argument.type)
        t = Thread(None, decr, args=(cl, cl))
    return t
