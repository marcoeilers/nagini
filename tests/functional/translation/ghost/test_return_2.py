# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def foo(i: int, gi: GInt) -> Tuple[int, GInt]:
    #:: ExpectedOutput(invalid.program:invalid.ghost.return)
    return gi, i
