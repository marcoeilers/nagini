"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 3, bottom left
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
    oldx = x
    while x > 0:
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)
        Invariant(TerminatesSif(x <= 0, 0))
        Invariant(x <= oldx)
        Invariant(Low(x > 0))
        _print(1)
        x -= 1
        if x == 0:
            while True:
                #:: ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.not_lowevent)
                Invariant(TerminatesSif(False, 0))
                pass

def main_fixed() -> None:
    Requires(LowEvent())
    x = inputPIN()
    Declassify(x > 0)
    oldx = x
    while x > 0:
        Invariant(TerminatesSif(x <= 0, 0))
        Invariant(x <= oldx)
        Invariant(Low(x > 0))
        _print(1)
        x -= 1
        Declassify(x == 0)
        if x == 0:
            while True:
                Invariant(TerminatesSif(False, 0))
                pass
