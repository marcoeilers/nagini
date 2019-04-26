# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def let_pure_method(i: int) -> None:
    Requires(Let(5, bool, lambda five: five > i))


def client_pure_method() -> None:
    let_pure_method(3)
    #:: ExpectedOutput(call.precondition:assertion.false)
    let_pure_method(6)


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val))


def let_impure_method(c: Cell) -> None:
    Requires(Let(c, bool, lambda cll: Acc(cll.val)))
    Ensures(Acc(c.val))
    Ensures(Let(c.val, bool, lambda v: v == 2))
    c.val = 2


def client_impure_method_success(c2: Cell) -> None:
    c1 = Cell()
    let_impure_method(c1)
    assert c1.val == 2
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    let_impure_method(c2)


def let_as_receiver(c: Cell, c3: Cell) -> None:
    Requires(Acc(Let(c, Cell, lambda c2: c2).val))
    c.val = 3
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    c3.val = 3