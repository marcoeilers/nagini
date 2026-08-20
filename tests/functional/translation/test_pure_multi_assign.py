# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def f(x: int) -> int:
    Ensures(Result() >= 0)
    #:: ExpectedOutput(unsupported:Multi-target assignments are not supported in pure functions.)
    a, b = x, x + 1
    return a
