# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def m1(a: int) -> bool:
    Ensures(Result() == (a > 5))
    return a != 5


def method_with_loop() -> int:
    Ensures(Result() == 10)
    i = 15
    sum = 0
    #:: ExpectedOutput(invalid.program:purity.violated)
    while m1(i):
        Invariant(sum == 15 - i)
        sum += 1
        i -= 1
    return sum
