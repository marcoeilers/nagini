# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from typing import NamedTuple

# 1 - ADTs with body
#:: ExpectedOutput(invalid.program:malformed.adt)
class ADT_5(ADT):
    def __init__(self) -> None:
        self.field = 5
