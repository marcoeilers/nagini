# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/returningObligations.chalice`` test from Chalice2Silver test
suite.
"""


from nagini_contracts.contracts import (
    Assert,
    Ensures,
    Invariant,
    Predicate,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


class ObjectLock(Lock[object]):
    @Predicate
    def invariant(self) -> bool:
        return True


def reAcq(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))
    Requires(MustRelease(a, 2))
    Ensures(MustRelease(a, 2))
    a.release()
    a.acquire()


def reAcq2(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Ensures(MustRelease(a, 2))


def reAcq3(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))
    Requires(MustRelease(a, 2))
    Ensures(MustRelease(a))
    a.release()
    a.acquire()


def reAcq4(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    #:: ExpectedOutput(postcondition.violated:insufficient.permission)
    Ensures(MustRelease(a))


def acq(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))
    Ensures(MustRelease(a, 5))
    a.acquire()


def continuous1(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    acq(a)

    while True:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(a, 3))
        Invariant(WaitLevel() < Level(a))
        a.release()
        a.acquire()
        reAcq(a)


def continuous2(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    acq(a)

    while True:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(a, 3))
        Invariant(WaitLevel() < Level(a))
        a.release()
        a.acquire()
        reAcq2(a)


def continuous3(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    acq(a)

    while True:
        Invariant(MustRelease(a, 3))
        Invariant(WaitLevel() < Level(a))
        a.release()
        a.acquire()
        reAcq3(a)