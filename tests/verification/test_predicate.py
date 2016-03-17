from py2viper_contracts.contracts import *


class Super:
    def __init__(self, a: int, b: int) -> None:
        Ensures(some_pred(self, a, 12))
        Ensures(Acc(self.field3))  # type: ignore
        Ensures(self.field3 == b) # type: ignore
        self.field = a
        self.field2 = 12
        self.field3 = b
        Fold(some_pred(self, a, 12))


@Predicate
def some_pred(r: Super, a: int, b: int) -> bool:
    return (Acc(r.field) and Acc(r.field2)) and (r.field == a and r.field2 == b)

def main() -> None:
    s = Super(34, 99)
    Unfold(some_pred(s, 34, 12))
    Assert(s.field == 34)
    Assert(s.field2 == 12)
    Assert(s.field3 == 99)
    s.field2 = 13
    Fold(some_pred(s, 34, 13))

def main_2() -> None:
    s = Super(34, 99)
    #:: ExpectedOutput(assert.failed:insufficient.permission)
    Assert(s.field == 34)
    Assert(s.field2 == 12)
    Assert(s.field3 == 99)
    s.field2 = 13
    Fold(some_pred(s, 34, 12))

def main_3() -> None:
    s = Super(34, 99)
    Unfold(some_pred(s, 34, 12))
    Assert(s.field == 34)
    Assert(s.field2 == 12)
    Assert(s.field3 == 99)
    #:: ExpectedOutput(fold.failed:assertion.false)
    Fold(some_pred(s, 34, 13))