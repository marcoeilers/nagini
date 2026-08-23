# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Optional
from nagini_contracts.contracts import *


class Inner:
    def __init__(self) -> None:
        self.top = 1
        Ensures(Acc(self.top) and self.top == 1)


class Outer:
    class Inner:
        def __init__(self, x: int) -> None:
            self.x = x
            Ensures(Acc(self.x) and self.x == x)

        @Pure
        def get(self) -> int:
            Requires(Acc(self.x, 1/2))
            Ensures(Result() == self.x)
            return self.x

    class Middle:
        class Deep:
            def __init__(self) -> None:
                self.d = 3
                Ensures(Acc(self.d) and self.d == 3)

    def __init__(self) -> None:
        self.i = Outer.Inner(5)
        Ensures(Acc(self.i) and Acc(self.i.x) and self.i.x == 5)


def construct_nested() -> None:
    n = Outer.Inner(7)
    Assert(n.get() == 7)


def construct_through_enclosing() -> None:
    o = Outer()
    Assert(o.i.x == 5)


def three_levels() -> None:
    d = Outer.Middle.Deep()
    Assert(d.d == 3)


# A nested class must not be confused with a top level class of the same name.
def shadowing() -> None:
    a = Inner()
    b = Outer.Inner(1)
    Assert(a.top == 1)
    Assert(not isinstance(a, Outer.Inner))
    Assert(not isinstance(b, Inner))


# Nested classes are usable as annotations, including inside other types.
def as_annotation(n: Outer.Inner, o: Optional[Outer.Inner]) -> int:
    Requires(Acc(n.x, 1/2))
    Ensures(Acc(n.x, 1/2))
    Ensures(Result() == n.x)
    return n.get()


def shadowing_fails() -> None:
    a = Inner()
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(isinstance(a, Outer.Inner))


def nested_field_fails() -> None:
    n = Outer.Inner(7)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(n.x == 8)
