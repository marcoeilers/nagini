"""
This is an example that illustrates Chalice2Silver
`issue 79 <https://bitbucket.org/viperproject/chalice2silver/issues/79/>`_.
"""


from threading import Lock

from py2viper_contracts.contracts import (
    Ensures,
    Implies,
    Invariant,
    Requires,
)
from py2viper_contracts.obligations import *


def test1() -> None:
    Requires(Implies(False, MustTerminate(1)))


def test2() -> None:
    while True:
        Invariant(Implies(False, MustTerminate(1)))
        pass
