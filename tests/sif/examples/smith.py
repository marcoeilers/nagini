"""
Example from "Principles of Secure Information Flow Analysis"
G. Smith
Malware Detection, 2007
"""

from nagini_contracts.contracts import *

def main(a: List[int], secret: int) -> int:
    Requires(list_pred(a))
    Requires(0 <= secret and secret < len(a))
    Requires(Low(a) and Forall(a, lambda e: e == 0))
    Ensures(Low(Result()))
    a[secret] = 1
    # for i in range(0, len(a)):
    i = 0
    while i < len(a):
        Invariant(list_pred(a))
        Invariant(0 <= i and i < len(a))
        Invariant(Low(i))
        if a[i] == 1:
            return i
