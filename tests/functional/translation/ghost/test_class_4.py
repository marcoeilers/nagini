# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

def reg_calls(gi: GInt) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    sub_cls = SubClass(gi)

class RegClass:
    def __init__(self, i: int) -> None:
        self.fld = i

class SubClass(RegClass):
    pass
