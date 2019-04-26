# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    @classmethod
    def construct(cls) -> 'A':
        Ensures(isinstance(Result(), cls))
        return cls()


class B(A):
    pass


class C(A):
    pass


def client() -> None:
    a = A.construct()
    Assert(isinstance(a, A))
    b = B.construct()
    Assert(isinstance(b, B))
    c = B()
    d = c.construct()
    Assert(isinstance(d, B))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(isinstance(b, C))


class D:
    def __init__(self) -> None:
        Ensures(self.state())
        self.val1 = 1
        Fold(self.state())

    @Predicate
    def state(self) -> bool:
        return Acc(self.val1) and self.val1 == 1

    @classmethod
    def construct(cls) -> 'D':
        Ensures(type(Result()) is cls)
        Ensures(Result().state())
        d = cls()
        return d

    some_field = 23

    @staticmethod
    def double(i: int) -> int:
        Ensures(Result() == i * 2)
        return i * 2

    @classmethod
    def access_static(cls) -> int:
        Ensures(Implies(cls is D, Result() == 46))
        return cls.double(cls.some_field)


class E(D):
    def __init__(self) -> None:
        Ensures(self.state())
        self.val1 = 1
        self.val2 = 2
        Fold(self.state())

    @Predicate
    def state(self) -> bool:
        return Acc(self.val2) and self.val2 == 2

    @classmethod
    def other_construct(cls) -> D:
        Ensures(type(Result()) is cls)
        Ensures(Result().state())
        return cls.construct()


def client_2() -> None:
    a = D.construct()
    Assert(isinstance(a, D))
    b = E.construct()
    assert isinstance(b, E)
    Unfold(b.state())
    b.val2 = 3
    Unfold(a.state())
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
