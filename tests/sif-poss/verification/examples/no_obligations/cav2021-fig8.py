# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock
from nagini_contracts.thread import Thread


class CellLock(Lock[object]):

    @Predicate
    def invariant(self) -> bool:
        return True


@ContractOnly
def _print(i: int) -> None:
    Requires(LowEvent())
    Requires(Low(i))

def thread1(l: CellLock) -> None:
    Requires(LowEvent())
    Requires(Low(l))
    l.acquire()
    _print(1)
    _print(1)
    l.release()

def thread2(l: CellLock) -> None:
    Requires(LowEvent())
    #:: ExpectedOutput(call.precondition:assertion.false)
    l.acquire()
    _print(2)
    _print(2)


def thread0(secret: bool) -> None:
    Requires(LowEvent())
    l1 = CellLock(object())
    l2 = CellLock(object())
    l = l1 if secret else l2
    t1 = Thread(target=thread1, args=(l1,))  # x aliases l2 depending on secret
    t2 = Thread(target=thread2, args=(l,))
    t1.start(thread1)
    t2.start(thread2)
