# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def regular_pair(i: int) -> Tuple[int, int]:
    return i, i

def mixed(i: int) -> Tuple[int, GInt]:
    # The returned value must have a ghost part as well.
    #:: ExpectedOutput(invalid.program:invalid.ghost.return)
    return regular_pair(i)
