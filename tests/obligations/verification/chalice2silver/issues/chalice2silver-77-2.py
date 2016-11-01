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


def test1() -> None:
    while False:
        Invariant(MustTerminate(0))
        pass

def test2() -> None:
    while True:
        Invariant(Implies(False, MustTerminate(0)))
        pass
