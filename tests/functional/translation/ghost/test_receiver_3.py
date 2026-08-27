# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GCellList = List['Cell']
MarkGhost(GCellList)


class Cell:
    def __init__(self) -> None:
        self.v = 0

    def bump(self) -> None:
        self.v = self.v + 1


def ghost_element_receiver(l: GCellList) -> None:
    # The receiver is an element of a ghost collection.
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    l[0].bump()
