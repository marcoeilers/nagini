"""
This is an example that illustrates Chalice2Silver
`issue 82 <https://bitbucket.org/viperproject/chalice2silver/issues/82/>`_.
"""


from py2viper_contracts.contracts import (
    Ensures,
    Import,
    Invariant,
    Requires,
)
from py2viper_contracts.obligations import *
from py2viper_contracts.lock import Lock
Import('lock')


def test1(l: Lock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    while True:
        Invariant(MustRelease(l, 1))
        Invariant(WaitLevel() < Level(l))
        do_release(l)
        l.acquire()


def test2(l: Lock) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 3))
    Requires(WaitLevel() < Level(l))
    while True:
        Invariant(MustRelease(l, 1))
        Invariant(WaitLevel() < Level(l))
        do_release(l)
        l.acquire()


def do_release(l: Lock) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 2))
    l.release()
