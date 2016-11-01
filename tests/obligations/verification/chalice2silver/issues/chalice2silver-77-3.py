"""
This is an example that illustrates Chalice2Silver
`issue 77 <https://bitbucket.org/viperproject/chalice2silver/issues/77/>`_.
"""


from threading import Lock

from py2viper_contracts.contracts import (
    Ensures,
    Implies,
    Invariant,
    Requires,
)
from py2viper_contracts.obligations import *


def test1(l: Lock) -> None:
    Requires(l is not None)
    l.acquire()
    while False:
        Invariant(MustRelease(l, 10 - 100))
        pass
    l.release()


def test2(l: Lock) -> None:
    Requires(l is not None)
    i = 0
    l.acquire()
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < 1:
        i += 1
    l.release()


def test3(l: Lock) -> None:
    Requires(l is not None)
    i = 0
    l.acquire()
    while i < 1:
        Invariant(MustRelease(l, 1 - i))
        i += 1
    l.release()
