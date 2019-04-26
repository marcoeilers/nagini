# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This is an example that illustrates Chalice2Silver
`issue 79 <https://bitbucket.org/viperproject/chalice2silver/issues/79/>`_.
"""


from nagini_contracts.contracts import (
    Implies,
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *


def test1() -> None:
    Requires(Implies(False, MustTerminate(1)))


def test2() -> None:
    while True:
        Invariant(Implies(False, MustTerminate(1)))
        pass
