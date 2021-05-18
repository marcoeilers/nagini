# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 2, top
"""

from nagini_contracts.contracts import *

def _print(val: int) -> None:
    Requires(LowEvent())
    Requires(Low(val))

def main(h: int) -> None:
    Requires(LowEvent())
    if h == 1:
        l = 42
    else:
        l = 17

    l = 0
    _print(l)
