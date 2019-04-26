# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    Assert,
    Implies,
    Invariant,
    Predicate,
    Requires,
    Ensures,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


# Positive examples.


class ObjectLock(Lock[object]):
    @Predicate
    def invariant(self) -> bool:
        return True


def await_1(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    i = 5
    while i > 0:
        Invariant(MustRelease(l))
        Invariant(WaitLevel() < Level(l))
        l.release()
        l.acquire()
        i -= 1
    l.release()


def await_2(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    Ensures(MustRelease(l))
    l.acquire()
    i = 5
    while i > 0:
        Invariant(MustRelease(l))
        Invariant(WaitLevel() < Level(l))
        l.release()
        l.acquire()
        i -= 1


# Obligations in method/loop body must be bounded.


def await_3(l: Lock[object]) -> None:
    Requires(MustRelease(l))
    Requires(WaitLevel() < Level(l))
    Ensures(MustRelease(l))
    i = 5
    while i > 0:
        #:: ExpectedOutput(invariant.not.established:insufficient.permission)
        Invariant(MustRelease(l))
        Invariant(WaitLevel() < Level(l))
        l.release()
        l.acquire()
        i -= 1


def await_4(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    Ensures(MustRelease(l))
    l.acquire()
    i = 5
    while i > 0:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(l))
        i -= 1


def infinite_recursion(l: Lock[object]) -> None:
    Requires(MustRelease(l))
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    infinite_recursion(l)


# Sometimes we do not have fresh obligation.


def no_obligation_1(l: Lock[object]) -> None:
    Requires(Implies(False, MustRelease(l)))
    Requires(l is not None)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    l.release()


def no_obligation_2(l: Lock[object]) -> None:
    Requires(l is not None)
    i = 5
    while i > 0:
        Invariant(Implies(False, MustRelease(l)))
        #:: ExpectedOutput(call.precondition:insufficient.permission)
        l.release()
        i -= 1


# Behavioral subtyping.


class A:

    def release(self, l: Lock[object]) -> None:
        Requires(MustRelease(l))
        l.release()


class ASub(A):

    def release(self, l: Lock[object]) -> None:
        Requires(MustRelease(l))
        l.release()


class B:

    #:: Label(B_release)
    def release(self, l: Lock[object]) -> None:
        Requires(MustRelease(l, 2))
        l.release()


class BSub(B):

    #:: ExpectedOutput(call.precondition:insufficient.permission, B_release)
    def release(self, l: Lock[object]) -> None:
        Requires(MustRelease(l))
        l.release()