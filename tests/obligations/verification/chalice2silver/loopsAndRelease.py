"""
This test is a ported version of
``obligations/loopsAndRelease.chalice`` test from Chalice2Silver test
suite.
"""


from py2viper_contracts.contracts import (
    Assert,
    Invariant,
    Requires,
)
from py2viper_contracts.obligations import *
from py2viper_contracts.lock import Lock


def rel_now(a: Lock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    a.release()


def rel_later(a: Lock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 10))
    a.release()


def f(a: Lock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    a.acquire()
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        i += 1
    a.release()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def f_leak(a: Lock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    a.acquire()
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        i += 1


def f_leak2(a: Lock) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    a.acquire()
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < n:
        i += 1
    a.release()
