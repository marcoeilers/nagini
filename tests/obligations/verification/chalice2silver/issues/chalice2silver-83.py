# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This is an example that illustrates Chalice2Silver
`issue 83 <https://bitbucket.org/viperproject/chalice2silver/issues/83/>`_.
"""


from nagini_contracts.contracts import (
    Ensures,
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


def foo(l: Lock[object]) -> None:
    Requires(MustRelease(l, 2))
    Ensures(MustRelease(l, 2))


def caller(l: Lock[object]) -> None:
    Requires(MustRelease(l, 3))
    Ensures(False)

    while True:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(l, 1))
        foo(l)