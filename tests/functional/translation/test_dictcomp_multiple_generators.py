# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Dict


def f(xs: List[int]) -> None:
    Requires(Acc(list_pred(xs)))
    #:: ExpectedOutput(unsupported:Multiple generators in dict comprehension.)
    d = {x: y for x in xs for y in xs}  # type: Dict[int, int]
