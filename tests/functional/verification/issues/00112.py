from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import List


def newlist() -> List[int]:
    Requires(MustTerminate(1))
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)|UnexpectedOutput(call.precondition:assertion.false, 112)|MissingOutput(leak_check.failed:caller.has_unsatisfied_obligations, 112)
    res = []  # type: List[int]
    return res

