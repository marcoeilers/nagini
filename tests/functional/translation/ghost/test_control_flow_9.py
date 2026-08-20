# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main(i: int, gi: GInt) -> int:
    if gi == 0:
        #:: ExpectedOutput(invalid.program:invalid.ghost.return)
        return i+1
    
    return i
