# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(28)
from nagini_contracts.contracts import *
from typing import Tuple


@GhostReturns(2)
def test() -> Tuple[int, int, int]:
    return 1, 2, 3
