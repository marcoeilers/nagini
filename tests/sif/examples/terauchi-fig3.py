"""
Example from "Secure Information Flow as a Safety Problem", Figure 3
T. Terauchi and A. Aiken
SAS 2005
"""

from nagini_contracts.contracts import *

@Pure
def hashfunc(i: int) -> int:
    return i

def main(secret: int, hash: int, input: int) -> int:
    Requires(Low(input))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    l = 0
    if hashfunc(input) == hash:
        l = secret
    return l

def main_fixed(secret: int, hash: int, input: int) -> int:
    Requires(Low(input))
    Ensures(Low(Result()))
    l = 0
    Declassify(secret if hashfunc(input) == hash else 0)
    if hashfunc(input) == hash:
        l = secret
    return l
