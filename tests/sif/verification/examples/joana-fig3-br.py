# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 3, bottom right
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
    while x == 0:
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)
        Invariant(TerminatesSif(x != 0, 0))
    _print(0)
    while x == 1:
        #:: ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.condition_not_low)
        Invariant(TerminatesSif(x != 1, 0))
    _print(0)
    while x == 2:
        #:: ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.condition_not_low)
        Invariant(TerminatesSif(x != 2, 0))
    _print(0)

def main_fixed() -> None:
    Requires(LowEvent())
    x = inputPIN()
    Declassify(x == 0)
    while x == 0:
        Invariant(TerminatesSif(x != 0, 0))
    _print(0)
    Declassify(x == 1)
    while x == 1:
        Invariant(TerminatesSif(x != 1, 0))
    _print(0)
    Declassify(x == 2)
    while x == 2:
        Invariant(TerminatesSif(x != 2, 0))
    _print(0)
