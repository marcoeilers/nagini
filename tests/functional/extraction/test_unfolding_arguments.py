# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Optional


class Node:
    def __init__(self, key: int) -> None:
        self.key = key
        self.left = None  # type: Optional[Node]


@Predicate
def tree(n: Node) -> bool:
    return Acc(n.key) and Acc(n.left)


def search(x: Optional[Node], k: int) -> int:
    Requires(Implies(x is not None, tree(x)))
    if x is None or Unfolding(tree(x), x.key == k):
        return k
    return search(Unfolding(tree(x), x.left), k)


def same(k: int) -> int:
    return k


def lengths(x: Node, xs: List[int]) -> int:
    Requires(tree(x) and Acc(list_pred(xs)))
    return len(Unfolding(tree(x), xs)) + same(Unfolding(tree(x), x.key))


class Box:
    def __init__(self, v: int) -> None:
        self.v = v


def boxed(x: Node) -> Box:
    Requires(tree(x))
    return Box(v=Unfolding(tree(x), x.key))
