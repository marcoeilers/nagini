# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def var_args(*args: int) -> int:
    return 0

def calls(gi: GInt) -> int:
    # Variadic parameters are always regular.
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    return var_args(1, gi)
