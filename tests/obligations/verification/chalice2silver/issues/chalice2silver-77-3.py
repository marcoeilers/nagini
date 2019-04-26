# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This is an example that illustrates Chalice2Silver
`issue 77 <https://bitbucket.org/viperproject/chalice2silver/issues/77/>`_.
"""


from nagini_contracts.contracts import (
    Ensures,
    Implies,
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def test1(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    while False:
        Invariant(MustRelease(l, 10 - 100))
        pass
    l.release()


def test2(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    i = 0
    l.acquire()
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < 1:
        i += 1
    l.release()


def test3(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    i = 0
    l.acquire()
    while i < 1:
        Invariant(MustRelease(l, 1 - i))
        i += 1
    l.release()