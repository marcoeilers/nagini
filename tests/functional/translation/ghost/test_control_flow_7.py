# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main(i: int, gi: GInt) -> int:
    while i > 0:
        i -= 1
        if gi == 6:
            #:: ExpectedOutput(invalid.program:invalid.ghost.break)
            break
    
    return i
