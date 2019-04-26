# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def m1(a: int) -> int:
    Ensures(Result() == 56)
    return 56


GLOBAL_VAR = m1(23)

OTHER_GLOBAL_VAR = 57

ANOTHER_GLOBAL_VAR = True

SO_MANY_GLOBAL_VARS = OTHER_GLOBAL_VAR if ANOTHER_GLOBAL_VAR else 44


@Pure
def m2() -> int:
    Ensures(Result() == 56 + 57)
    return GLOBAL_VAR + SO_MANY_GLOBAL_VARS


def impure() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 55)
    return GLOBAL_VAR
