# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This is an example that illustrates Chalice2Silver
`issue 82 <https://bitbucket.org/viperproject/chalice2silver/issues/82/>`_.
"""


from nagini_contracts.contracts import (
    Ensures,
    Invariant,
    Predicate,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


class ObjectLock(Lock[object]):
    @Predicate
    def invariant(self) -> bool:
        return True


def test1(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    while True:
        Invariant(MustRelease(l, 1))
        Invariant(WaitLevel() < Level(l))
        do_release(l)
        l.acquire()


def test2(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 3))
    Requires(WaitLevel() < Level(l))
    while True:
        Invariant(MustRelease(l, 1))
        Invariant(WaitLevel() < Level(l))
        do_release(l)
        l.acquire()


def do_release(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(MustRelease(l, 2))
    l.release()