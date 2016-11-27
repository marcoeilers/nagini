"""
This is an example that illustrates Chalice2Silver
`issue 82 <https://bitbucket.org/viperproject/chalice2silver/issues/82/>`_.
"""


from threading import Lock

from py2viper_contracts.contracts import (
    Ensures,
    Invariant,
    Requires,
)
from py2viper_contracts.obligations import *


def test1(l: Lock) -> None:
    Requires(l is not None)
    l.acquire()
    while True:
        Invariant(MustRelease(l, 1))
        do_release(l)
        l.acquire()


def test2(l: Lock) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 3))
    while True:
        Invariant(MustRelease(l, 1))
        do_release(l)
        l.acquire()


def do_release(l: Lock) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 2))
    l.release()
