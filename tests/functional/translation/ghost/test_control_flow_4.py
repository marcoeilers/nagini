# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

def main(i: int, gi: GInt) -> None:
    if i > 0:
        i += 1
        if gi != 5:
            gi = 0
        else:
            if i >= 2:
                #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
                i = 6
