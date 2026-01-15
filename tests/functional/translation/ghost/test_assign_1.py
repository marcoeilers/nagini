# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

def main(i: int, gi: GInt) -> None:
    res: GInt = gi + i
    j = i + 2 
    i += 1 
    gi += 1

    i, gi = i+1, gi+1
