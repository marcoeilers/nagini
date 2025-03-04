# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional

class Fac:
    @Opaque
    @Pure
    def fac1(self, i: int) -> int:
        Decreases(i)
        if i <= 1:
            return 1
        return i * self.fac1(i - 1)

    @Opaque
    @Pure
    def fac2(self, i: int) -> int:
        Decreases(8)
        if i <= 1:
            return 1
        #:: ExpectedOutput(termination.failed:tuple.false)
        return i * self.fac2(i - 1)


    @Opaque
    @Pure
    def fac3(self, i: int) -> int:
        Decreases(None)
        if i <= 1:
            return 1
        return i * self.fac3(i - 1)


    @Opaque
    @Pure
    def fac4(self, i: int) -> int:
        Decreases(i)
        if i <= 1:
            return 1
        #:: ExpectedOutput(termination.failed:termination.condition.false)
        return i * self.fac4h(i - 1)

    @Opaque
    @Pure
    def fac4h(self, i: int) -> int:
        if i <= 1:
            return 1
        return i * self.fac4h(i - 1)


    @Opaque
    @Pure
    def fac5(self, i: int) -> int:
        Decreases(i)
        if i < 0:
            #:: ExpectedOutput(termination.failed:tuple.false)|ExpectedOutput(carbon)(termination.failed:tuple.false)
            return self.fac5(i)
        if i <= 1:
            return 1
        return i * self.fac5(i - 1)


    @Opaque
    @Pure
    def fac5w(self, i: int) -> int:
        Decreases(None)
        if i < 0:
            return self.fac5w(i)
        if i <= 1:
            return 1
        return i * self.fac5w(i - 1)

    @Opaque
    @Pure
    def fac5cond(self, i: int) -> int:
        Decreases(i, i >= 0)
        if i < 0:
            return self.fac5cond(i)
        if i <= 1:
            return 1
        return i * self.fac5cond(i - 1)


    @Opaque
    @Pure
    def fac5pre(self, i: int) -> int:
        Requires(i >= 0)
        Decreases(i)
        if i < 0:
            return self.fac5pre(i)
        if i <= 1:
            return 1
        return i * self.fac5pre(i - 1)


class Node:
    def __init__(self) -> None:
        self.value = 0
        self.next : Optional[Node] = None


class Do:
    @Predicate
    def tree(self, n: Node) -> bool:
        return (
            Acc(n.next) and Acc(n.value) and Implies(n.next is not None, self.tree(n.next))
        )


    @Opaque
    @Pure
    def size1(self, n: Node) -> int:
        Requires(self.tree(n))
        Decreases(self.tree(n))
        if Unfolding(self.tree(n), n.next) is None:
            return 1
        return 1 + Unfolding(self.tree(n), self.size1(n.next))

#    @Opaque
#    @Pure
#    def size2(self, n: Node) -> int:
#        Requires(self.tree(n))
#        Decreases(self.tree(n))
#        if Unfolding(self.tree(n), n.next) is None:
#            return 1
#        #:: ExpectedOutput(termination.failed:tuple.false)
#        return 1 + self.size2(n)

# Basic
class A:
    @Opaque
    @Pure
    #:: Label(L1)
    def foo(self, i: int) -> int:
        Decreases(1)
        return i ** 2

class B(A):
    @Opaque
    @Pure
    def foo(self, i: int) -> int:
        Decreases(1)
        return i ** 2 + 1

# subclass overrides foo but doesn't promise to terminate
class C(A):
    @Opaque
    @Pure
    #:: ExpectedOutput(termination.failed:termination.condition.false,L1)
    def foo(self, i: int) -> int:
        return i ** 2 + 2


# overridden function doesn't terminate
class W:
    @Opaque
    @Pure
    def foo(self, i: int) -> int:
        # no Decreases
        return i ** 2

# overriding function can terminate or not
class X(W):
    @Opaque
    @Pure
    def foo(self, i: int) -> int:
        Decreases(7)
        return i ** 2

class Y(W):
    @Opaque
    @Pure
    def foo(self, i: int) -> int:
        return i ** 2