# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

def main() -> None:
    t = (0, 1)
    gi: GInt = 0
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    i, gi = t
