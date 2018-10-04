"""
Example from paper "Modular Product Programs"
M. Eilers, P. Müller, S. Hitz
ESOP 2018
"""
from typing import List

from nagini_contracts.contracts import *

def is_female(person: int) -> int:
    Ensures(Implies(Low(person % 2), Low(Result())))
    gender = person % 2
    if gender == 0:
        return 1
    return 0

def main(people: List[int]) -> int:
    Requires(list_pred(people))
    Requires(Low(len(people)))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(people), Low(people[i] % 2)), [[people[i]]])))
    Ensures(Low(Result()))

    i = 0
    count = 0
    while i < len(people):
        Invariant(list_pred(people))
        Invariant(i >= 0 and i <= len(people))
        Invariant(Low(i))
        Invariant(Low(count))
        Invariant(Low(len(people)))
        Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(people), Low(people[i] % 2)), [[people[i]]])))
        current = people[i]
        female = is_female(current)
        count += female
        i += 1
    return count
