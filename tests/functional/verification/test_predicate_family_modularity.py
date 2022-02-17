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
    Fold(x.state())


class SubX(X):

    @Predicate #:: ExpectedOutput(predicate.not.wellformed:family.member.not.framed)
    def state(self, i: int) -> bool:
        return 1 > 0 and self.f1 > 0 and 5 > 2
