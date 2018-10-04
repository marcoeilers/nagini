"""
Example from "A Separation Logic for Enforcing Declarative Information Flow Control Policies"
D. Costanzo and Z. Shao
POST 2014
"""

from nagini_contracts.contracts import *
from typing import List

def _print(val: int) -> None:
    Requires(LowEvent())
    Requires(Low(val))

def main(A: List[int]) -> None:
    Requires(LowEvent())
    Requires(list_pred(A))
    Requires(len(A) == 64)
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(A), Low(A[i] == 0)))))
    i = 0
    while i < 64:
        Invariant(0 <= i and i <= 64)
        Invariant(Low(i))
        Invariant(list_pred(A))
        Invariant(len(A) == 64)
        Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(A), Low(A[i] == 0)))))
        x = A[i]
        if x == 0:
            _print(i)
        i += 1
