# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def m() -> int:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Decreases(2)
    return 2
