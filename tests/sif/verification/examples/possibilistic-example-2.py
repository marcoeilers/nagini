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
    Requires(TerminatesSif(True, 1))

def thread1(l: CellLock) -> None:
    Requires(LowEvent())
    Requires(Low(l))
    Requires(TerminatesSif(True, 2))
    l.acquire()
    _print(1)
    _print(1)
    l.release()

def thread2(l: CellLock) -> None:
    Requires(LowEvent())
    Requires(TerminatesSif(True, 2))
    # fail
    l.acquire()
    _print(2)
    _print(2)


def thread0(secret: bool) -> None:
    Requires(LowEvent())
    Requires(TerminatesSif(True, 2))
    l1 = CellLock(object())
    l2 = CellLock(object())
    l = l1 if secret else l2
    t1 = Thread(target=thread1, args=(l1,))  # x aliases l2 depending on secret
    t2 = Thread(target=thread2, args=(l,))
    t1.start(thread1)
    t2.start(thread2)
