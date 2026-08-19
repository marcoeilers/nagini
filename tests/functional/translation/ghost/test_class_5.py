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


def ghost_class_argument(g: GCell, i: int) -> int:
    # The argument is of a ghost type, so reading from it yields ghost values.
    gi: GInt = g.get()
    return i

def forward_reference(g: 'GCell', i: int) -> int:
    gi: GInt = g.get()
    return i
