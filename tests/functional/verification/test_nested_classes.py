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


# A reference cannot tell whether the name it uses will turn out to be a nested
# class, so the placeholder it creates has to be adopted by the declaration.
class Holder:
    def make(self) -> 'Thing':
        Ensures(Acc(Result().n) and Result().n == 1)
        return Holder.Thing()

    class Thing:
        def __init__(self) -> None:
            self.n = 1
            Ensures(Acc(self.n) and self.n == 1)


# Declared after Holder.Thing, and unrelated to it. Inside Holder the name
# Thing refers to the nested class, which is what mypy resolves it to as well.
class Thing:
    def __init__(self) -> None:
        self.m = 2
        Ensures(Acc(self.m) and self.m == 2)


def forward_reference_to_nested(h: Holder) -> None:
    a = h.make()
    Assert(a.n == 1)
    Assert(isinstance(a, Holder.Thing))
    Assert(not isinstance(a, Thing))


def module_level_stays_separate() -> None:
    b = Thing()
    Assert(b.m == 2)
    Assert(not isinstance(b, Holder.Thing))


def forward_reference_to_nested_f(h: Holder) -> None:
    a = h.make()
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(isinstance(a, Thing))


# Static fields in an enclosing and a nested class, which must keep working:
# only a name clash between a static field and a method or class is rejected.
class WithStatics:
    limit = 10

    class Nested:
        size = 3

        def get(self) -> int:
            Ensures(Result() == 3)
            return WithStatics.Nested.size

    def under(self, v: int) -> bool:
        Ensures(Result() == (v < 10))
        return v < WithStatics.limit


def static_fields_in_nested_classes() -> None:
    Assert(WithStatics.limit == 10)
    Assert(WithStatics.Nested.size == 3)
    n = WithStatics.Nested()
    g = n.get()
    Assert(g == 3)
