"""
This test is a ported version of
``obligations/aliasingRelease.chalice`` test from Chalice2Silver
test suite.
"""


from threading import Lock

from py2viper_contracts.contracts import (
    Assert,
    Requires,
)
from py2viper_contracts.obligations import *


def rel_now(a: Lock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(MustTerminate(2))
    a.release()


def rel_later(a: Lock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 5))
    Requires(MustTerminate(2))
    a.release()


def f(a: Lock, b: Lock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a == b)
    Requires(MustRelease(a, 3))
    rel_now(b)


def f_fail(a: Lock, b: Lock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a == b)
    Requires(MustRelease(a, 3))
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    rel_later(b)


def fprecond(a: Lock, b: Lock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a == b)
    Requires(MustRelease(a, 2))
    Requires(MustRelease(b, 2))

    # Precondition is False.
    Assert(False)


def f_ok(a: Lock, b: Lock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 8))

    if a == b:
        Assert(False)

    rel_later(a)
    rel_later(b)


def f_leak(a: Lock, b: Lock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 3))

    # TODO: Find out why Silicon needs this additional assert. Is this
    # an instance of conjunctive aliasing problem?
    Assert(a != b)

    rel_now(b)
    rel_later(a)


def f_ok_1(a: Lock, b: Lock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is not b)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 3))

    rel_now(b)
    rel_later(a)


def af(a: Lock, b: Lock) -> None:
    Requires(MustRelease(a, 2))
    if a == b:
        b.release()
    else:
        a.release()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def af_leak(a: Lock, b: Lock) -> None:
    Requires(MustRelease(a, 2))

    if a == b:
        b.release()
