# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.thread import (
    Thread, MayStart, getArg, getMethod, Joinable, ThreadPost, getOld, arg
)


def printTwice(x: int) -> None:
    pass


def client(t: Thread) -> None:
    #:: ExpectedOutput(invalid.program:concurrency.in.sif)
    t.start(printTwice)
