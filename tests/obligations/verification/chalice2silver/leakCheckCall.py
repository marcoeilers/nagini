# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a not-fully ported version of
``obligations/leakCheckCall.chalice`` test from Chalice2Silver
test suite.

.. note::

    Channel related test parts were omitted.
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


def t() -> None:
    pass


def s() -> None:
    Requires(MustTerminate(1))


def g(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    t()
    a.release()


def g1(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    s()
    a.release()


def g2(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    a.release()
    t()


def g3(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    s()
    a.release()
    t()


def h1(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    t()
    a.release()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def h2(a: ObjectLock) -> None:
    Requires(MustTerminate(5))
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    s()


def h3(a: ObjectLock) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    t()
    a.release()