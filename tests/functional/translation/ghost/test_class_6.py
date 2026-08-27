# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Ghost
class GCell:
    def __init__(self) -> None:
        self.v = 0

    @Pure
    def get(self) -> int:
        return self.v


def ghost_class_argument(g: GCell) -> int:
    #:: ExpectedOutput(invalid.program:invalid.ghost.return)
    return g.get()
