# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


# Only two components are supported for mixed return types.
#:: ExpectedOutput(invalid.program:invalid.ghost.annotation)
def three_parts(i: int, gi: GInt) -> Tuple[int, GInt, int]:
    return i, gi, i
