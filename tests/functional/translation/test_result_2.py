# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def some_int() -> int:
    #:: ExpectedOutput(invalid.program:incorrect.declared.type)
    Ensures(ResultT(str) is None)
    return 4