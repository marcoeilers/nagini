# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Optional
from nagini_contracts.contracts import *


class Node:
    def __init__(self, val: int) -> None:
        self.val = val
        self.next = None  # type: Optional[Node]
        Ensures(Acc(self.val) and Acc(self.next))
        Ensures(self.val == val and self.next is None)


class Holder:
    def __init__(self, root: Node) -> None:
        self.root = root
        Ensures(Acc(self.root) and self.root is root)

    def get(self) -> Node:
        Requires(Acc(self.root) and Acc(self.root.val) and self.root.val > 0)
        Ensures(Acc(self.root) and Result() is self.root and Acc(self.root.val) and self.root.val > 0)
        return self.root


def ident(n: Node) -> Node:
    Requires(Acc(n.val))
    Ensures(Result() is n and Acc(n.val) and n.val == Old(n.val))
    return n


def pick(a: Node, b: Node, first: bool) -> Node:
    Requires(Acc(a.val) and Acc(b.val))
    Ensures(Acc(a.val) and Acc(b.val))
    Ensures(Implies(a is not Result(), b is Result() and b.val == Old(b.val)))
    Ensures(Implies(a is Result(), a.val == Old(a.val)))
    if first:
        return a
    return b


def other(n: Node, m: Optional[Node]) -> Optional[Node]:
    Requires(Acc(n.val))
    Requires(Implies(m is not None, Acc(m.val)))
    Ensures(Acc(n.val))
    Ensures(Implies(m is not None, Acc(m.val)))
    Ensures(Implies(m is Result() and m is not None, m.val == Old(m.val)))
    return m


class Leaf(Node):
    def __init__(self, val: int) -> None:
        self.val = val
        self.next = None
        self.weight = 1
        Ensures(Acc(self.val) and Acc(self.next) and Acc(self.weight))


def narrowed(n: Node) -> Node:
    Requires(Acc(n.weight) if isinstance(n, Leaf) else True)
    Ensures((n is Result() and Acc(n.weight)) if isinstance(n, Leaf) else True)
    return n


class Failure(Exception):
    def __init__(self, code: int) -> None:
        self.code = code
        Ensures(Acc(self.code) and self.code == code)


def fail(e: Failure) -> None:
    Requires(Acc(e.code))
    Ensures(False)
    Exsures(Failure, e is RaisedException() and Acc(e.code) and e.code == Old(e.code))
    raise e
