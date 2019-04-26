# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread, MayStart, getArg, getMethod, ThreadPost, getOld, arg
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
    cl = Cell()
    #:: ExpectedOutput(invalid.program:invalid.thread.creation)
    t = Thread(target=decr, group=None, args=(cl, 6, 8))
    return t