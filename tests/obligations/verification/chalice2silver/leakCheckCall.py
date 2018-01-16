"""
This test is a not-fully ported version of
``obligations/leakCheckCall.chalice`` test from Chalice2Silver
test suite.

.. note::

    Channel related test parts were omitted.
"""


from nagini_contracts.contracts import (
    Assert,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def t() -> None:
    pass


def s() -> None:
    Requires(MustTerminate(1))


def g(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(a.invariant())

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    t()
    a.release()


def g1(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(a.invariant())

    s()
    a.release()


def g2(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(a.invariant())

    a.release()
    t()


def g3(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(a.invariant())

    s()
    a.release()
    t()


def h1(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(a.invariant())

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    t()
    a.release()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def h2(a: Lock[object]) -> None:
    Requires(MustTerminate(5))
    Requires(a is not None)
    Requires(MustRelease(a, 2))

    s()


def h3(a: Lock[object]) -> None:
    Requires(a is not None)
    Requires(MustRelease(a, 2))
    Requires(a.invariant())

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    t()
    a.release()
