# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This is an example that illustrates Chalice2Silver
`issue 77 <https://bitbucket.org/viperproject/chalice2silver/issues/77/>`_.
"""


from nagini_contracts.contracts import (
    Invariant,
    Requires,
)
from nagini_contracts.obligations import *


def test(n: int) -> None:
    Requires(n > 1)
    i = 0
    while i < n:
        Invariant(MustTerminate(n - i))
        i += 1
