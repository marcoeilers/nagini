# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def reg_calls(gi: GInt) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    reg(i=0, k=gi, gh=0)

def reg(i: int, gh: GInt, k: int) -> None:
    pass