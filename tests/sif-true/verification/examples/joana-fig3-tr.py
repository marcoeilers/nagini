# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 3, top right
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
    willterm = x >= 0 # type: bool
    while x != 0:
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)
        Invariant(TerminatesSif(x >= 0, x if x >= 0 else 0))
        Invariant(willterm.__eq__(x >= 0))
        x -= 1
    _print(1)

def main_fixed() -> None:
    Requires(LowEvent())
    x = inputPIN()
    Declassify(x >= 0)
    willterm = x >= 0 # type: bool
    while x != 0:
        Invariant(TerminatesSif(x >= 0, x if x >= 0 else 0))
        Invariant(willterm.__eq__(x >= 0))
        x -= 1
    _print(1)
