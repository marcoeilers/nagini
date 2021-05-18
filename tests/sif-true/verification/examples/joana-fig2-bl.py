# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 2, bottom left
"""

from nagini_contracts.contracts import *

def _print(val: int) -> None:
    Requires(LowEvent())
    Requires(Low(val))

def f(x: int) -> int:
    Ensures(Implies(Low(x), Low(Result())))
    return x + 42

def main(h: int) -> None:
    Requires(LowEvent())
    l = 2
    x = f(h)
    y = f(l)
    _print(y)
