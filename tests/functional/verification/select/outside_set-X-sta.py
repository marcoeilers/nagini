from nagini_contracts.contracts import *


class X:
    def __init__(self) -> None:
        self.f1 = 1
        Ensures(Acc(self.f1))

    @Predicate
    def state(self, i: int) -> bool:
        return Acc(self.f1)


def outside_set(x: X) -> None:
    Requires(Acc(x.f1) and x.f1 > 0)
    #:: ExpectedOutput(fold.failed:unknown.family.receiver.type)
    Fold(x.state(0))


class SubX(X):

    @Predicate #:: ExpectedOutput(predicate.not.wellformed:family.member.not.framed)
    def state(self, i: int) -> bool:
        return 1 > 0 and self.f1 > 0 and 5 > 2


class Y:
    def __init__(self) -> None:
        self.f1 = 1
        Ensures(Acc(self.f1))

    @Predicate
    def state(self, i: int) -> bool:
        return Acc(self.f1)


def outside_setY(x: Y) -> None:
    Requires(Acc(x.f1) and x.f1 > 0)
    #ExpectedOutput(fold.failed:unknown.family.receiver.type)  # not selected
    Fold(x.state(0))


class SubY(Y):

    @Predicate #ExpectedOutput(predicate.not.wellformed:family.member.not.framed)  # not selected
    def state(self, i: int) -> bool:
        return 1 > 0 and self.f1 > 0 and 5 > 2


class Z:
    def __init__(self) -> None:
        self.f1 = 1
        Ensures(Acc(self.f1))

    @Predicate
    def sta(self, i: int) -> bool:
        return Acc(self.f1)


def outside_setZ(x: Z) -> None:
    Requires(Acc(x.f1) and x.f1 > 0)
    #ExpectedOutput(fold.failed:unknown.family.receiver.type)  # not selected
    Fold(x.sta(0))


class SubZ(Z):

    @Predicate #:: ExpectedOutput(predicate.not.wellformed:family.member.not.framed)
    def sta(self, i: int) -> bool:
        return 1 > 0 and self.f1 > 0 and 5 > 2

