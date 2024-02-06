# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Dict, Any


class Parent:
    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z
        Ensures(Acc(self.x) and self.x == x)
        Ensures(Acc(self.y) and self.y == y)
        Ensures(Acc(self.z) and self.z == z)
        Ensures(MayCreate(self.d))

    @Predicate
    def pred_parent(self) -> bool:
        return type(self) == Parent and Acc(self.z) and self.z > 0

    @Predicate
    def pred_fam(self) -> bool:
        return Acc(self.x) and self.x > 0

    @Pure
    def __getattr__(self, item) -> int:
        Ensures(Result() > 10)


class Child(Parent):
    def __init__(self, x: int, y: int, z: int) -> None:
        super().__init__(x, y, z)
        Ensures(Acc(self.x) and self.x == x)
        Ensures(Acc(self.y) and self.y == y)
        Ensures(Acc(self.z) and self.z == z)
        Ensures(Acc(self.d))

    @Predicate
    def pred_child(self) -> bool:
        return type(self) == Child and Acc(self.z) and self.z < 0

    @Predicate
    def pred_fam(self) -> bool:
        return Acc(self.y) and self.y > 0

    @Pure
    def __getattr__(self, item) -> int:
        Ensures(Result() > 20)


def my_func_1(c: Child) -> None:
    Requires(Acc(c.pred_fam()))
    Ensures(Acc(c.pred_fam()))

    Unfold(Acc(c.pred_fam(), 1/2))
    Assert(c.x > 0)
    Assert(c.y > 0)
    Fold(Acc(c.pred_fam(), 1/2))

    return


def my_func_2(p: Parent) -> None:
    Requires(Acc(p.pred_parent()))
    Ensures(Acc(p.pred_parent()))

    Unfold(Acc(p.pred_parent(), 1/2))
    Assert(p.z > 0)
    Fold(Acc(p.pred_parent(), 1 / 2))
    return


def my_func_3(c: Child) -> None:
    Requires(Acc(c.pred_child()))
    Ensures(Acc(c.pred_child()))

    Unfold(Acc(c.pred_child(), 1/2))
    Assert(c.z < 0)
    Fold(Acc(c.pred_child(), 1 / 2))
    return


def main() -> None:
    p = Parent(x=1, y=1, z=1)
    c = Child(x=1, y=1, z=-1)

    Fold(p.pred_fam())
    Fold(c.pred_fam())
    Fold(p.pred_parent())
    Fold(c.pred_child())

    Assert(Unfolding(Acc(p.pred_fam(), 1 / 2), p.x > 0))
    Assert(p.d > 10)
    Assert(c.d > 20)

    my_func_1(c)
    my_func_2(c)
    my_func_3(p)

    # Assert(10 == 15)      # sanity check


if __name__ == "__main__":
    main()

