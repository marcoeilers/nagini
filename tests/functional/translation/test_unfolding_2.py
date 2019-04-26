# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional


class Cell:
    def __init__(self) -> None:
        self.val = None  # type: Optional[Cell]


@Predicate
def P(c: Cell) -> bool:
    return Acc(c.val)


def client(c: Cell) -> None:
    Requires(Unfolding(P(c), c.val is not None))
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Requires(Unfolding(P(c), Acc(c.val.val)))