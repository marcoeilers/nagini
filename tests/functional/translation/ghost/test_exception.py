# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

@Ghost
def main(gi: GInt) -> None:
    if gi < 0:
        #:: ExpectedOutput(invalid.program:invalid.ghost.raise)
        raise NotImplementedError()
    
    # Do something regular
