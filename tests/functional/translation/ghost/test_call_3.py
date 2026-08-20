# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def reg_calls(gi: GInt) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    i = reg_but_ghost_return()

def reg_but_ghost_return() -> GInt:
    pass