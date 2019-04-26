# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/loopsAndTermination.chalice`` test from Chalice2Silver
test suite.

.. note::

    Fork statements were omitted.
"""


from nagini_contracts.contracts import (
    Assert,
    Requires,
    Invariant,
    Implies,
)
from nagini_contracts.obligations import *


def x() -> None:
    pass


def y() -> None:
    Requires(MustTerminate(1))


def z() -> None:
    Requires(MustTerminate(5))
    y()


def f() -> None:
    while True:
        pass


def f1() -> None:
    Requires(MustTerminate(10))
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while True:
        pass


def f2() -> None:
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        i += 1


def f3() -> None:
    Requires(MustTerminate(5))
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        i += 1


def f4() -> None:
    Requires(MustTerminate(5))
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < n:
        i += 1


def f5() -> None:
    Requires(MustTerminate(5))
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        i += 1
        j = 0
        #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
        while j < n:
            j += 1


def f6() -> None:
    Requires(MustTerminate(5))
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        i += 1
        j = 0
        while j < n:
            Invariant(MustTerminate(n-j+1))
            j += 1


def f7() -> None:
    Requires(MustTerminate(5))
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < n:
        i += 1
        # fork x()
        # fork y()
        # fork z()
        x()
        j = 0
        while j < n:
            Invariant(MustTerminate(n-j+1))
            j += 1


def f8() -> None:
    Requires(MustTerminate(5))
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < n:
        i += 1
        j = 0
        while j < n:
            Invariant(MustTerminate(n-j+1))
            j += 1


def f9() -> None:
    i = 0
    n = 10
    while i < n:
        i += 1
        x()
        y()
        z()
        j = 0
        while j < n:
            Invariant(MustTerminate(n-j+1))
            j += 1


def f10() -> None:
    i = 0
    n = 10
    while i < n:
        i += 1
        x()
        y()
        z()
        j = 0
        while j < n:
            Invariant(MustTerminate(n-j+1))
            y()
            j += 1
