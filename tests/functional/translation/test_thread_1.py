# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread, MayStart, getArg, getMethod, ThreadPost, getOld, arg
from nagini_contracts.obligations import MustTerminate, WaitLevel, Level, MustRelease, BaseLock


def noop(l: BaseLock) -> int:
    Requires(MustRelease(l))
    Ensures(MustRelease(l))
    pass


def client_fork(t: Thread, l: BaseLock) -> None:
    Requires(Acc(MayStart(t)))
    Requires(getMethod(t) == noop)
    Requires(l is getArg(t, 0))
    Ensures(WaitLevel() < Level(t))
    #:: ExpectedOutput(invalid.program:invalid.thread.start)
    t.start(noop)