# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def m1(a: int) -> int:
    Ensures(Result() == 56)
    return 56


@Pure
def f1(b: int) -> int:
    #:: ExpectedOutput(invalid.program:purity.violated)
    Ensures(Result() == m1(b))
    return 56
