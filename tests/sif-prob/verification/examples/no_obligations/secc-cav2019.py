# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example adapted from "SecCSL: Security Concurrent Separation Logic"
G. Ernst and T. Murray
CAV 2019
https://bitbucket.org/covern/secc/src/master/examples/case-studies/
"""

from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock

class Record:
    def __init__(self, ic: bool, data: int) -> None:
        self.is_classified = ic
        self.data = data


class Mutex(Lock[Record]):

    @Predicate
    def invariant(self) -> bool:
        return (Acc(self.get_locked().is_classified) and
                Acc(self.get_locked().data) and
                Low(self.get_locked().is_classified) and
                Implies(not self.get_locked().is_classified, Low(self.get_locked().data)))


# Models OUTPUT_REG from the SecCSL paper
def output(i: int) -> None:
    Requires(Low(i))


def thread1(r: Record, m: Mutex) -> None:
    Requires(m.get_locked() is r and Low(m))
    while True:
        m.acquire()
        if not r.is_classified:
            output(r.data)
        m.release()


def thread2(r: Record, m: Mutex) -> None:
    Requires(m.get_locked() is r and Low(m))
    m.acquire()
    r.is_classified = False
    r.data = 0
    m.release()


def thread1_insecure(r: Record, m: Mutex) -> None:
    Requires(m.get_locked() is r and Low(m))
    while True:
        m.acquire()
        if r.is_classified:  # BUG
            #:: ExpectedOutput(call.precondition:assertion.false)
            output(r.data)
        m.release()


def thread2_insecure(r: Record, m: Mutex) -> None:
    Requires(m.get_locked() is r and Low(m))
    m.acquire()
    r.is_classified = False
    # BUG: r.data = 0
    #:: ExpectedOutput(fold.failed:sif.fold)
    m.release()
