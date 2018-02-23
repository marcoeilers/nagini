"""
This test is a ported version of
``obligations/aliasingRelease.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Assert,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def rel_now(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(MustTerminate(2))
    Requires(a.invariant())
    a.release()


def rel_later(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 5))
    Requires(MustTerminate(2))
    Requires(a.invariant())
    a.release()


def f(a: Lock[object], b: Lock[object]) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is b)
    Requires(MustRelease(a, 3))
    Requires(a.invariant())
    rel_now(b)


def f_fail(a: Lock[object], b: Lock[object]) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is b)
    Requires(MustRelease(a, 3))
    Requires(b.invariant())
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    rel_later(b)


def fprecond(a: Lock[object], b: Lock[object]) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is b)
    Requires(MustRelease(a, 2))
    Requires(MustRelease(b, 2))

    # Precondition is False.
    Assert(False)


def f_ok(a: Lock[object], b: Lock[object]) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 8))
    Requires(a.invariant())
    Requires(b.invariant())

    if a is b:
        Assert(False)

    rel_later(a)
    rel_later(b)


def f_leak(a: Lock[object], b: Lock[object]) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 3))
    Requires(a.invariant())
    Requires(b.invariant())

    # TODO: Find out why Silicon needs this additional assert. Is this
    # an instance of conjunctive aliasing problem?
    Assert(a is not b)

    rel_now(b)
    rel_later(a)


def f_ok_1(a: Lock[object], b: Lock[object]) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is not b)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 3))
    Requires(a.invariant())
    Requires(b.invariant())

    rel_now(b)
    rel_later(a)


def af(a: Lock[object], b: Lock[object]) -> None:
    Requires(MustRelease(a, 2))
    Requires(a.invariant())
    if a is b:
        b.release()
    else:
        a.release()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def af_leak(a: Lock[object], b: Lock[object]) -> None:
    Requires(MustRelease(a, 2))
    Requires(a.invariant())

    if a is b:
        b.release()