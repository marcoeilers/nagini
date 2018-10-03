"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 3, top left
"""

from nagini_contracts.contracts import *

def _print(val: int) -> None:
    Requires(LowEvent())
    Requires(Low(val))

def inputPIN() -> int:
    return 17

def main() -> None:
    Requires(LowEvent())
    x = inputPIN()
    while x > 0:
        Invariant(TerminatesSif(True, x if x > 0 else 0))
        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)|ExpectedOutput(carbon)(call.precondition:assertion.false)
        _print(0)
        x -= 1
    while True:
        Invariant(TerminatesSif(False, 0))

def main_fixed() -> None:
    Requires(LowEvent())
    x = inputPIN()
    while x > 0:
        Invariant(TerminatesSif(True, x if x > 0 else 0))
        x -= 1
    while True:
        Invariant(TerminatesSif(False, 0))
