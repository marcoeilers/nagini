"""
This test is a ported version of
``obligations/lifetime.chalice`` test from Chalice2Silver
test suite.
"""


from py2viper_contracts.contracts import (
    Assert,
    Import,
    Requires,
)
from py2viper_contracts.obligations import *
from py2viper_contracts.lock import Lock
Import('lock')


def do_release(l: Lock) -> None:
    Requires(l is not None)
    #:: Label(do_release__MustTerminate)
    Requires(MustRelease(l, 0))

    l.release()


def do_release_caller(l: Lock) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 1))

    #:: ExpectedOutput(call.precondition:obligation_measure.non_positive)
    do_release(l)
