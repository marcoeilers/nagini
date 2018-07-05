"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 1, top left
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
    if x < 1234:
        #:: ExpectedOutput(carbon)(call.precondition:assertion.false)
        _print(0)
    y = x
    #:: ExpectedOutput(call.precondition:assertion.false)
    _print(y)

def main_fixed() -> None:
    Requires(LowEvent())
    x = inputPIN()
    Declassify(x < 1234)
    if x < 1234:
        _print(0)
    y = x
    Declassify(x)
    _print(y)
