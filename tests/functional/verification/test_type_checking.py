# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from nagini_contracts.contracts import *

if TYPE_CHECKING:
    from typing import List

if typing.TYPE_CHECKING:
    from typing import Optional


class Node:
    def __init__(self, value: int, next: Node | None = None) -> None:
        self.value = value
        self.next = next
        Ensures(Acc(self.value) and self.value == value)
        Ensures(Acc(self.next) and self.next is next)


def first(xs: List[int], d: int | None) -> int | None:
    Requires(Acc(list_pred(xs)))
    Ensures(Acc(list_pred(xs)))
    Ensures(Implies(len(xs) == 0, Result() is d))
    if len(xs) > 0:
        return xs[0]
    return d


def value(n: None | Node, d: Optional[int]) -> int:
    Requires(Implies(n is not None, Acc(n.value)))
    Ensures(Implies(n is not None, Acc(n.value) and Result() == Old(n.value)))
    Ensures(Implies(n is None and d is None, Result() == 0))
    if n is not None:
        return n.value
    if d is not None:
        return d
    return 0


def shadowed(TYPE_CHECKING: bool) -> int:
    Ensures(Implies(TYPE_CHECKING, Result() == 1))
    if TYPE_CHECKING:
        return 1
    return 2


def client() -> None:
    n = Node(3, Node(4))
    assert value(n, None) == 3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert value(None, 5) == 0
