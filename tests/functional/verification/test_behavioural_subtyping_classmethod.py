# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        #:: ExpectedOutput(postcondition.violated:assertion.false, L1)
        Ensures(Acc(self.val) and self.val > 13)  # type: ignore
        self.val = 16

    @classmethod
    def construct(cls) -> 'A':
        Ensures(isinstance(Result(), cls))
        return cls()


class B(A):
    def __init__(self) -> None:
        Ensures(Acc(self.val) and self.val > 14)  # type: ignore
        self.val = 16


class C(A):
    #:: Label(L1)
    def __init__(self) -> None:
        Ensures(Acc(self.val) and self.val > 12)  # type: ignore
        self.val = 16


class D:
    def __init__(self) -> None:
        Ensures(Acc(self.val) and self.val > 9)  # type: ignore
        self.val = 14

    @classmethod
    def construct(cls) -> 'D':
        Ensures(isinstance(Result(), cls))
        #:: ExpectedOutput(postcondition.violated:assertion.false, L2)
        Ensures(Acc(Result().val) and Result().val > 7)
        return cls()


class E(D):
    @classmethod
    def construct(cls) -> D:
        Ensures(isinstance(Result(), cls))
        Ensures(Acc(Result().val) and Result().val > 8)
        return cls()


class F(D):
    #:: Label(L2)
    @classmethod
    def construct(cls) -> D:
        Ensures(isinstance(Result(), cls))
        Ensures(Acc(Result().val) and Result().val > 6)
        return cls()
