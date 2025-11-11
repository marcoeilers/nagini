# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class Cell:
    def __init__(self, i: int) -> None:
        self.val = i
        Ensures(Acc(self.val) and self.val is i)


@Pure
def testing1(c: Cell, b: bool) -> int:
    Requires(Implies(b, pos(c)))
    Ensures(Result() > 0)
    if b:
        #:: ExpectedOutput(invalid.program:invalid.contract.call)
        Unfold(True)
        return c.val
    return 3