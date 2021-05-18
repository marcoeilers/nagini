# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "Secure Information Flow as a Safety Problem", Figure 4
T. Terauchi and A. Aiken
SAS 2005
"""

from nagini_contracts.contracts import *

def main(n: int, k: int) -> int:
    Requires(n > 0)
    Requires(Low(n))
    Requires(Low(k))
    Ensures(Low(Result()))
    f1 = 1
    f2 = 0
    while (n > 0):
        Invariant(Low(n))
        Invariant(Low(f1))
        Invariant(Low(f2))
        f1 = f1 + f2
        f2 = f1 - f2
        n -= 1
    if f1 > k:
        return 1
    return 0
