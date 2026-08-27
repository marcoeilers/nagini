# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Cell:
    def __init__(self) -> None:
        self.v = 0

    def bump(self) -> None:
        self.v = self.v + 1

    @Pure
    def get(self) -> int:
        return self.v


GCell = Cell
MarkGhost(GCell)


def reg_receiver(c: Cell) -> int:
    c.bump()
    return c.get()

def ghost_receiver(g: GCell) -> None:
    # Calling a pure function on a ghost receiver yields a ghost value.
    gi: GInt = g.get()

@Ghost
class GhostCell:
    def __init__(self) -> None:
        self.v = 0

    def bump(self) -> None:
        self.v = self.v + 1

@Ghost
def ghost_cell_receiver(g: GhostCell) -> None:
    g.bump()
