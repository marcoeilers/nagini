# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/aliasingRelease.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Assert,
    Predicate,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


class ObjectLock(Lock[object]):
    @Predicate
    def invariant(self) -> bool:
        return True


def rel_now(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(MustTerminate(2))
    a.release()


def rel_later(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 5))
    Requires(MustTerminate(2))
    a.release()


def f(a: ObjectLock, b: ObjectLock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is b)
    Requires(MustRelease(a, 3))
    rel_now(b)


def f_fail(a: ObjectLock, b: ObjectLock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is b)
    Requires(MustRelease(a, 3))
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    rel_later(b)


def fprecond(a: ObjectLock, b: ObjectLock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is b)
    Requires(MustRelease(a, 2))
    Requires(MustRelease(b, 2))

    # Precondition is False.
    Assert(False)


def f_ok(a: ObjectLock, b: ObjectLock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 8))

    if a is b:
        Assert(False)

    rel_later(a)
    rel_later(b)


def f_leak(a: ObjectLock, b: ObjectLock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 3))

    # TODO: Find out why Silicon needs this additional assert. Is this
    # an instance of conjunctive aliasing problem?
    Assert(a is not b)

    rel_now(b)
    rel_later(a)


def f_ok_1(a: ObjectLock, b: ObjectLock) -> None:
    Requires(a is not None)
    Requires(b is not None)
    Requires(a is not b)
    Requires(MustRelease(a, 7))
    Requires(MustRelease(b, 3))

    rel_now(b)
    rel_later(a)


def af(a: ObjectLock, b: ObjectLock) -> None:
    Requires(MustRelease(a, 2))
    if a is b:
        b.release()
    else:
        a.release()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def af_leak(a: ObjectLock, b: ObjectLock) -> None:
    Requires(MustRelease(a, 2))

    if a is b:
        b.release()