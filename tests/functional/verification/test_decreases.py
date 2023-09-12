# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional

@Pure
def fac1(i: int) -> int:
    Decreases(i)
    if i <= 1:
        return 1
    return i * fac1(i - 1)

@Pure
def fac2(i: int) -> int:
    Decreases(8)
    if i <= 1:
        return 1
    #:: ExpectedOutput(termination.failed:tuple.false)
    return i * fac2(i - 1)


@Pure
def fac3(i: int) -> int:
    Decreases(None)
    if i <= 1:
        return 1
    return i * fac3(i - 1)


@Pure
def fac4(i: int) -> int:
    Decreases(i)
    if i <= 1:
        return 1
    #:: ExpectedOutput(termination.failed:termination.condition.false)
    return i * fac4h(i - 1)

@Pure
def fac4h(i: int) -> int:
    if i <= 1:
        return 1
    return i * fac4h(i - 1)


@Pure
def fac5(i: int) -> int:
    Decreases(i)
    if i < 0:
        #:: ExpectedOutput(termination.failed:tuple.false)|ExpectedOutput(carbon)(termination.failed:tuple.false)
        return fac5(i)
    if i <= 1:
        return 1
    return i * fac5(i - 1)


@Pure
def fac5w(i: int) -> int:
    Decreases(None)
    if i < 0:
        return fac5w(i)
    if i <= 1:
        return 1
    return i * fac5w(i - 1)

@Pure
def fac5cond(i: int) -> int:
    Decreases(i, i >= 0)
    if i < 0:
        return fac5cond(i)
    if i <= 1:
        return 1
    return i * fac5cond(i - 1)


@Pure
def fac5pre(i: int) -> int:
    Requires(i >= 0)
    Decreases(i)
    if i < 0:
        return fac5pre(i)
    if i <= 1:
        return 1
    return i * fac5pre(i - 1)


class Node:
    def __init__(self) -> None:
        self.value = 0
        self.next : Optional[Node] = None


@Predicate
def tree(n: Node) -> bool:
    return (
        Acc(n.next) and Acc(n.value) and Implies(n.next is not None, tree(n.next))
    )


@Pure
def size1(n: Node) -> int:
    Requires(tree(n))
    Decreases(tree(n))
    if Unfolding(tree(n), n.next) is None:
        return 1
    return 1 + Unfolding(tree(n), size1(n.next))


@Pure
def size2(n: Node) -> int:
    Requires(tree(n))
    Decreases(tree(n))
    if Unfolding(tree(n), n.next) is None:
        return 1
    #:: ExpectedOutput(termination.failed:tuple.false)
    return 1 + size2(n)
