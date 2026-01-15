# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple

GInt = int
MarkGhost(GInt)

#:: ExpectedOutput(invalid.program:invalid.ghost.annotation)
def main(gi: GInt) -> Tuple[GInt, int]:
    pass