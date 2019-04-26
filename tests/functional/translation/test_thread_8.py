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


@Pure
def get(c: Cell) -> int:
    Requires(Acc(c.val))
    return c.val


def client_fork(t: Thread) -> None:
    #:: ExpectedOutput(invalid.program:invalid.thread.start)
    t.start(get)