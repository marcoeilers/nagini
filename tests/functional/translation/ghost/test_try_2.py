# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Ghost
def ghost_try(x: int) -> int:
    # Exception handling is not available in ghost code.
    #:: ExpectedOutput(invalid.program:invalid.ghost.try)
    try:
        x = x + 1
    except Exception:
        x = 2
    return x
