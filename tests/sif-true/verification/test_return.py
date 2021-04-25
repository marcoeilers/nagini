# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def m1() -> int:
    Requires(LowEvent())
    Ensures(Low(Result()))
    return 0

def m2() -> None:
    return

def m3(secret: bool) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    if secret:
        return 0
    else:
        return 1

def m4() -> int:
    Ensures(Result() == 1)
    return 1
    return 12
