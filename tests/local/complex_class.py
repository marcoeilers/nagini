# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Any

# using this will generate
#   self_5 := self_1
#   arg_13 := self_1
#   arg_15 := self_0
# inside Child___init__, where self_0 is not found
# and should be self_1, just like the two lines above it
# @Complex
# class Grandparent:
#     def __init__(self) -> None:
#         self.x = 1
#         Ensures(Acc(self.x))
#         Ensures(self.x > 0)


@Complex
class Parent:
    def __init__(self) -> None:
        self.x = "15"
        self.y = 20
        Ensures(Acc(self.x))
        Ensures(self.x == "15")
        Ensures(Acc(self.y))
        Ensures(self.y == 20)
        # Ensures(MayCreate(self, 'y'))
        # Ensures(MayCreate(self, 'z'))


class Child(Parent):
    def __init__(self) -> None:
        super().__init__()
        Ensures(Acc(self.x))
        Ensures(self.x == "15")
        Ensures(Acc(self.y))
        Ensures(self.y == 20)


class Normal:
    def __init__(self) -> None:
        self.x = "25"
        Ensures(Acc(self.x))
        Ensures(self.x == "25")


def some_func(c: Parent) -> None:
    Requires(Acc(c.x))
    Requires(Acc(c.y))
    c.x = "30"
    c.y = 40
    Ensures(Acc(c.x))
    Ensures(c.x == "30")
    Ensures(Acc(c.y))
    Ensures(c.y == 40)


def main() -> None:
    c = Child()
    Assert(c.x == "15")
    Assert(c.y == 20)
    some_func(c)


if __name__ == "__main__":
    main()



