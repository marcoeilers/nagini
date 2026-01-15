# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

def reg_calls() -> None:
    reg_cls = RegClass(0)
    sub_cls = SubClass(0)
    
    loc = RegClass.static
    loc = reg_cls.static
    sub_cls.reg()

@Ghost
def ghost_calls() -> None:
    gh_cls = GhostClass()
    gi = gh_cls.ghost()
    gh_sub_cls = Ghost_Subclass()

class RegClass:
    static = 0
    
    def __init__(self, i: int) -> None:
        self.fld = i

    def reg(self) -> None:
        pass

class SubClass(RegClass):
    pass

@Ghost
class GhostClass:
    def ghost(self) -> int:
        return 0

@Ghost
class Ghost_Subclass(GhostClass):
    pass