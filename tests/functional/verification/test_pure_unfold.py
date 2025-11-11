# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class Cell:
    def __init__(self, i: int) -> None:
        self.val = i
        Ensures(Acc(self.val) and self.val is i)

@Predicate
def pos(c: Cell) -> bool:
    return Acc(c.val) and c.val > 0

@Pure
def testing1(c: Cell, b: bool) -> int:
    Requires(Implies(b, pos(c)))
    Ensures(Result() > 0)
    if b:
        Unfold(pos(c))
        return c.val
    return 3


@Pure  #:: ExpectedOutput(not.wellformed:insufficient.permission)
def testing2(c: Cell, b: bool) -> int:
    Ensures(Result() > 0)
    if b:
        Unfold(pos(c))  # fail no perm
        return c.val
    return 3

@Pure
def testing3(c: Cell, b: bool) -> int:
    Requires(Implies(b, pos(c)))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 1)
    if b:
        Unfold(Acc(pos(c)))
        return c.val
    return 3


@Pure  #:: ExpectedOutput(not.wellformed:insufficient.permission)
def testing4(c: Cell, b: bool) -> int:
    Requires(Implies(b, pos(c)))
    Ensures(Result() > 0)
    if b:
        return 4
    Unfold(Acc(pos(c)))
    return c.val


@Pure
def testing5(c: Cell, b: bool) -> int:
    Requires(Implies(not b, pos(c)))
    Ensures(Result() > 0)
    if b:
        return 4
    Unfold(Acc(pos(c)))
    return c.val
