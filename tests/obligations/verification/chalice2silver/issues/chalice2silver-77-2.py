# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This is an example that illustrates Chalice2Silver
`issue 77 <https://bitbucket.org/viperproject/chalice2silver/issues/77/>`_.
"""


from nagini_contracts.contracts import (
    Implies,
    Invariant,
)
from nagini_contracts.obligations import *


def test1() -> None:
    while False:
        Invariant(MustTerminate(0))
        pass

def test2() -> None:
    while True:
        Invariant(Implies(False, MustTerminate(0)))
        pass
