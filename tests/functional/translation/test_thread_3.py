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


@Predicate
def get(c: Cell) -> bool:
    return Acc(c.val)


def client_create(b: bool) -> Thread:
    cl = Cell()
    #:: ExpectedOutput(invalid.program:invalid.thread.creation)
    t = Thread(target=get, group=None, args=(cl,))
    return t