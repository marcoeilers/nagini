# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

def main(i: int, gi: GInt) -> None:
    j = i
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    j += gi
