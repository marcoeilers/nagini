# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def match_sequence(x: List[int]) -> int:
    #:: ExpectedOutput(unsupported:sequence patterns not yet supported)
    match x:
        case [a, b]:
            return a + b
        case _:
            return 0
