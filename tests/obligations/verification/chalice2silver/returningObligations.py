"""
This test is a ported version of
``obligations/returningObligations.chalice`` test from Chalice2Silver test
suite.
"""


from nagini_contracts.contracts import (
    Assert,
    Ensures,
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def reAcq(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))
    Requires(MustRelease(a, 2))
    Requires(a.invariant())
    Ensures(MustRelease(a, 2))
    Ensures(a.invariant())
    a.release()
    a.acquire()


def reAcq2(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Ensures(MustRelease(a, 2))


def reAcq3(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))
    Requires(MustRelease(a, 2))
    Requires(a.invariant())
    Ensures(MustRelease(a))
    Ensures(a.invariant())
    a.release()
    a.acquire()


def reAcq4(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    #:: ExpectedOutput(postcondition.violated:insufficient.permission)
    Ensures(MustRelease(a))


def acq(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))
    Ensures(MustRelease(a, 5))
    Ensures(a.invariant())
    a.acquire()


def continuous1(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    acq(a)

    while True:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(a, 3))
        Invariant(WaitLevel() < Level(a))
        Invariant(a.invariant())
        a.release()
        a.acquire()
        reAcq(a)


def continuous2(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    acq(a)

    while True:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(a, 3))
        Invariant(WaitLevel() < Level(a))
        Invariant(a.invariant())
        a.release()
        a.acquire()
        reAcq2(a)


def continuous3(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    acq(a)

    while True:
        Invariant(MustRelease(a, 3))
        Invariant(WaitLevel() < Level(a))
        Invariant(a.invariant())
        a.release()
        a.acquire()
        reAcq3(a)