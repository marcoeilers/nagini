from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        self.a = 12
        Ensures(Acc(self.a))
        Ensures(MayCreate(self, 'b'))

    def set(self, v: int) -> None:
        Requires(MaySet(self, 'b'))
        self.b = v
        Ensures(Acc(self.b) and self.b == v)

    def set2(self, v: int) -> None:
        Requires(MayCreate(self, 'b'))
        self.b = v
        Ensures(Acc(self.b))


@Predicate
def pred1() -> bool:
    return True


@Predicate
def pred2(x: A, f: float) -> bool:
    return Acc(x.a) and MayCreate(x, 'b') and MaySet(x, 'c') and x.a == 14


@Predicate
def pred3(x: A, y: int, z: float) -> bool:
    return Acc(x.a) and x.a == 14 and pred1()


@Native
@ContractOnly
def somemethod() -> int:
    Requires(True)
    Ensures(True)
