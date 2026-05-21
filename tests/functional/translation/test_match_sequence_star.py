# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def match_sequence_star(x: List[int]) -> int:

    match x:  #:: ExpectedOutput(unsupported:sequence patterns not yet supported)
        case [head, *tail]:
            return head
        case _:
            return 0
