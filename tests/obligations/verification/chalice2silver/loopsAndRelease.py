"""
This test is a ported version of
``obligations/loopsAndRelease.chalice`` test from Chalice2Silver test
suite.
"""


from nagini_contracts.contracts import (
    Assert,
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def rel_now(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(a.invariant())
    a.release()


def rel_later(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 10))
    Requires(a.invariant())
    a.release()


def f(a: Lock[object]) -> None:
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
def f_leak(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    a.acquire()
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        i += 1


def f_leak2(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(WaitLevel() < Level(a))

    a.acquire()
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < n:
        i += 1
    a.release()