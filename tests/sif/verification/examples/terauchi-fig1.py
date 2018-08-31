"""
Example from "Secure Information Flow as a Safety Problem", Figure 1
T. Terauchi and A. Aiken
SAS 2005
"""

from nagini_contracts.contracts import *

def main(h: bool, y: int) -> int:
    Requires(Low(y))
    Ensures(Low(Result()))
    z = 1
    if h:
        x = 1
    else:
        x = z
    return x + y
