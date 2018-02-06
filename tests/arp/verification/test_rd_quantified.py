from nagini_contracts.contracts import *


class Clazz:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        Ensures(Acc(self.y))
        self.x = 5  # type: int
        self.y = 3  # type: int
        self.seq = Sequence(self)  # type: Sequence[Clazz]

    def m1(self) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        Ensures(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        self.m1()

    def m1_1(self) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        Ensures(Rd(self.seq) and Forall(self.seq, lambda r: Rd(r.x)))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)
        self.m1()

    def m2(self) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        self.m1()

    def m2_1(self) -> None:
        Requires(self != None)
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        Requires(Rd(self.seq) and Forall(self.seq, lambda r: Acc(r.x)))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)
        self.m1()
