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


def test(n: int) -> None:
    Requires(n > 1)
    i = 0
    while i < n:
        Invariant(MustTerminate(n - i))
        i += 1
