from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)

class Foo:
    def __init__(self, i: GInt) -> None:
        self.gi : GInt = i

def bar(i: int, gi: GInt) -> GInt:
    res: GInt = gi + i
    return res
