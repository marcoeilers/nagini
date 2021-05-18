# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "Principles of Secure Information Flow Analysis"
G. Smith
Malware Detection, 2007
"""

from nagini_contracts.contracts import *
from typing import List

def main(a: List[int], secret: int) -> int:
    Requires(list_pred(a))
    Requires(0 <= secret and secret < len(a))
    Requires(Low(a) and Low(len(a)))
    Requires(Forall(int, lambda el: (Implies(el >= 0 and el < len(a), a[el] is 0), [[a[el]]])))
    Ensures(Low(Result()))
    a[secret] = 1
    # for i in range(0, len(a)):
    i = 0
    while i < len(a):
        Invariant(list_pred(a))
        Invariant(LowExit() and Low(len(a)))
        Invariant(0 <= i and i <= len(a))
        #:: ExpectedOutput(invariant.not.established:assertion.false)
        Invariant(Forall(int, lambda el: (Implies(el >= 0 and el < len(a), Low(a[el])), [[a[el]]])))
        Invariant(Low(i))
        if a[i] == 1:
            return i
        i += 1
    return 0

def main_fixed(a: List[int], secret: int) -> int:
    Requires(list_pred(a))
    Requires(0 <= secret and secret < len(a))
    Requires(Low(a) and Low(len(a)) and Forall(int, lambda el: (Implies(el >= 0 and el < len(a), a[el] is 0), [[a[el]]])))
    Ensures(Low(Result()))
    a[secret] = 1
    Declassify(secret)
    i = 0
    asd = [12]
    while i < len(a):
        Invariant(list_pred(a))
        Invariant(LowExit() and Low(len(a)))
        Invariant(0 <= i and i <= len(a))
        Invariant(Forall(int, lambda el: (Implies(el >= 0 and el < len(a), Low(a[el])), [[a[el]]])))
        Invariant(Low(i))
        if a[i] == 1:
            return i
        i += 1
    return 0
