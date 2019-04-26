# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

x = 2
x = 4

def m() -> int:
    Ensures(Result() == 2)
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Requires(x == 2)
    return 2
