# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "A new algorithm for low-deterministic security"
D. Giffhorn and G. Snelting
International Journal of Information Security, 2015
Figure 13, left
"""

from nagini_contracts.contracts import Ensures, Low, Result

def inputPIN() -> int:
    return 17

def main(h: int) -> int:
    Ensures(Low(Result()))
    h = inputPIN()
    if h < 0:
        l = 0
    else:
        l = 0
    return l
