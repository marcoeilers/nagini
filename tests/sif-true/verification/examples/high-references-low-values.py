# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def add_zero_incorrect(i: int, secret: int) -> int:
    Requires(Low(i))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    if secret == 0:
        return i + 0
    return i


def add_zero_correct(i: int, secret: int) -> int:
    Requires(Low(i))
    Ensures(LowVal(Result()))
    if secret == 0:
        return i + 0
    return i