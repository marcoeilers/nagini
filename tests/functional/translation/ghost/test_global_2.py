# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


g_counter: GInt = 0


def leak() -> int:
    #:: ExpectedOutput(invalid.program:invalid.ghost.return)
    return g_counter
