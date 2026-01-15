# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

#:: ExpectedOutput(invalid.program:invalid.ghost.annotation)
def main(i: int, gi: GInt, *args: GInt) -> None:
    pass