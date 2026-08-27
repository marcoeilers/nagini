# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


# A return type combining a regular and a ghost part must have the form
# Tuple[<regular type>, <ghost type>].
#:: ExpectedOutput(invalid.program:invalid.ghost.annotation)
def ghost_first(i: int, gi: GInt) -> Tuple[GInt, int]:
    return gi, i
