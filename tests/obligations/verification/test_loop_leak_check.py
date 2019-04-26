# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Requires,
    Implies,
    Invariant,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def MustInvoke_context_1(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < 5:
        i += 1


def MustRelease_context_1(lock: Lock[object]) -> None:
    Requires(MustRelease(lock, 1))
    i = 0
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < 5:
        i += 1


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def MustInvoke_context_2(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def MustRelease_context_2(lock: Lock[object]) -> None:
    Requires(MustRelease(lock, 1))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def MustInvoke_body_1(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(token(t1, 1))
        i += 1


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def MustRelease_body_1(lock: Lock[object]) -> None:
    Requires(MustRelease(lock, 1))
    i = 0
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(lock, 1))
        i += 1


def MustInvoke_body_2(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    #:: ExpectedOutput(carbon)(leak_check.failed:loop_body.leaks_obligations)
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(Implies(i < 5, token(t1, 1)))
        i += 1


def MustRelease_body_2(lock: Lock[object]) -> None:
    Requires(MustRelease(lock, 1))
    i = 0
    #:: ExpectedOutput(carbon)(leak_check.failed:loop_body.leaks_obligations)
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(Implies(i < 5, MustRelease(lock, 1)))
        i += 1