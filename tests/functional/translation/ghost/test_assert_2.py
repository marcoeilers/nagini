# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Ghost
def ghost_main(i: int) -> None:
    # Ghost code cannot contain a runtime assert either.
    #:: ExpectedOutput(invalid.program:invalid.ghost.assert)
    assert i == 0
