# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import List


def newlist() -> List[int]:
    Requires(MustTerminate(1))
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    res = []  # type: List[int]
    return res

