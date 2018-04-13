"""
This is an example that illustrates Chalice2Silver
`issue 82 <https://bitbucket.org/viperproject/chalice2silver/issues/82/>`_.
"""


from nagini_contracts.contracts import (
    Ensures,
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def test1(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    while True:
        Invariant(MustRelease(l, 1))
        Invariant(WaitLevel() < Level(l))
        Invariant(l.invariant())
        do_release(l)
        l.acquire()


def test2(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 3))
    Requires(WaitLevel() < Level(l))
    Requires(l.invariant())
    while True:
        Invariant(MustRelease(l, 1))
        Invariant(WaitLevel() < Level(l))
        Invariant(l.invariant())
        do_release(l)
        l.acquire()


def do_release(l: Lock[object]) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 2))
    Requires(l.invariant())
    l.release()