# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from nagini_contracts.contracts import *

def power3_A(input: int) -> int:
    Requires(input>0)
    Ensures(Result() == input ** input )
    out_a = input
    for i in range(input - 1):
        Invariant(out_a == input ** (len(Previous(i)) + 1))
        out_a = out_a * input
    return out_a