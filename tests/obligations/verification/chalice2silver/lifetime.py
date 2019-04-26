# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/lifetime.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Assert,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def do_release(l: Lock[object]) -> None:
    Requires(l is not None)
    #:: Label(do_release__MustTerminate)
    Requires(MustRelease(l, 0))

    l.release()


def do_release_caller(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 1))

    #:: ExpectedOutput(call.precondition:obligation_measure.non_positive)
    do_release(l)