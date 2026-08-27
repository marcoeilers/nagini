# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple

GPair = Tuple[int, int]
MarkGhost(GPair)


def unpack_ghost_pair(p: GPair) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    a, b = p
