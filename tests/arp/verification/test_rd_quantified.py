# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Clazz:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        Ensures(Acc(self.y))
        self.x = 5  # type: int
        self.y = 3  # type: int
        self.seq = PSeq(self)  # type: PSeq[Clazz]

    def m1(self, b: bool) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        Ensures(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        if b:
            self.m1(b)

    def m1_1(self, b: bool) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        Ensures(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)
        if b:
            self.m1(b)

    def m2(self, b: bool) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        if b:
            self.m1(b)

    def m2_1(self, b: bool) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)
        if b:
            self.m1(b)
