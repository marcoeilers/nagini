"""
This is an example that illustrates Chalice2Silver
`issue 83 <https://bitbucket.org/viperproject/chalice2silver/issues/83/>`_.
"""


from threading import Lock

from py2viper_contracts.contracts import (
    Ensures,
    Invariant,
    Requires,
)
from py2viper_contracts.obligations import *


def foo(l: Lock) -> None:
    Requires(MustRelease(l, 2))
    Ensures(MustRelease(l, 2))


def caller(l: Lock) -> None:
    Requires(MustRelease(l, 3))
    Ensures(False)

    while True:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(MustRelease(l, 1))
        foo(l)
