# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Ghost
class GhostCell:
    def __init__(self) -> None:
        self.value = 0


class RegularCell:
    def __init__(self) -> None:
        self.value = 0
        self.gvalue: GInt = 0

    def update(self, i: int) -> None:
        Requires(Acc(self.value) and Acc(self.gvalue))
        Ensures(Acc(self.value) and Acc(self.gvalue))
        self.value = i
        self.gvalue = i
