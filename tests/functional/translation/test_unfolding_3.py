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
    #:: ExpectedOutput(invalid.program:purity.violated)
    a = Unfolding(P(c), get_val(c))


def get_val(c: Cell) -> int:
    return 4
