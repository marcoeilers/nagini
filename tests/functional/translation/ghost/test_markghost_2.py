# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)
#:: ExpectedOutput(type.error:MarkGhost may only define ghost names once.)
MarkGhost(GInt)

def main(gi: GInt) -> None:
    gi += 1
