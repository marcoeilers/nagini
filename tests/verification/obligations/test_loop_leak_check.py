from py2viper_contracts.contracts import (
    Requires,
    Implies,
    Import,
    Invariant,
)
from py2viper_contracts.io import *
from py2viper_contracts.obligations import *
from py2viper_contracts.lock import Lock
Import('lock')


def MustInvoke_context_1(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < 5:
        i += 1


def MustRelease_context_1(lock: Lock) -> None:
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
def MustRelease_context_2(lock: Lock) -> None:
    Requires(MustRelease(lock, 1))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1


#:: OptionalOutput(leak_check.failed:method_body.leaks_obligations)
def MustInvoke_body_1(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(token(t1, 1))
        i += 1


#:: OptionalOutput(leak_check.failed:method_body.leaks_obligations)
def MustRelease_body_1(lock: Lock) -> None:
    Requires(MustRelease(lock, 1))
    i = 0
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(lock, 1))
        i += 1


def MustInvoke_body_2(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    #:: OptionalOutput(leak_check.failed:loop_body.leaks_obligations)
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(Implies(i < 5, token(t1, 1)))
        i += 1


def MustRelease_body_2(lock: Lock) -> None:
    Requires(MustRelease(lock, 1))
    i = 0
    #:: OptionalOutput(leak_check.failed:loop_body.leaks_obligations)
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(Implies(i < 5, MustRelease(lock, 1)))
        i += 1
