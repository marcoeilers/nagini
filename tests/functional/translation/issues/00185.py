# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def crash() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Invariant(True)