from threading import Lock

from py2viper_contracts.contracts import (
    Acc,
    Assert,
    Invariant,
    Implies,
    Requires,
    Ensures,
)
from py2viper_contracts.obligations import *


# Positive examples.


def await_1(l: Lock) -> None:
    Requires(l is not None)
    l.acquire()
    i = 5
    while i > 0:
        Invariant(MustRelease(l))
        l.release()
        l.acquire()
        i -= 1
    l.release()


def await_2(l: Lock) -> None:
    Requires(l is not None)
    Ensures(MustRelease(l))
    l.acquire()
    i = 5
    while i > 0:
        Invariant(MustRelease(l))
        l.release()
        l.acquire()
        i -= 1


# Obligations in method/loop body must be bounded.


def await_3(l: Lock) -> None:
    Requires(MustRelease(l))
    Ensures(MustRelease(l))
    i = 5
    while i > 0:
        #:: ExpectedOutput(invariant.not.established:insufficient.permission)
        Invariant(MustRelease(l))
        l.release()
        l.acquire()
        i -= 1


def await_4(l: Lock) -> None:
    Requires(l is not None)
    Ensures(MustRelease(l))
    l.acquire()
    i = 5
    while i > 0:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(l))
        i -= 1


def infinite_recursion(l: Lock) -> None:
    Requires(MustRelease(l))
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    infinite_recursion(l)


# Sometimes we do not have fresh obligation.


def no_obligation_1(l: Lock) -> None:
    Requires(Implies(False, MustRelease(l)))
    Requires(l is not None)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    l.release()


def no_obligation_2(l: Lock) -> None:
    Requires(l is not None)
    i = 5
    while i > 0:
        Invariant(Implies(False, MustRelease(l)))
        #:: ExpectedOutput(call.precondition:insufficient.permission)
        l.release()
        i -= 1
