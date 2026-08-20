# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Cell:
    def __init__(self) -> None:
        self.v = 0

    def bump(self) -> None:
        self.v = self.v + 1


GCell = Cell
MarkGhost(GCell)


def ghost_receiver(g: GCell) -> None:
    # The receiver does not exist at runtime, so an impure method cannot be
    # called on it.
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    g.bump()
