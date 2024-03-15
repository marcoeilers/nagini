# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Any


@Complex
class Parent:
    def __init__(self) -> None:
        self.x = "15"
        self.y = 20
        Ensures(Acc(self.x))
        Ensures(self.x == "15")
        Ensures(Acc(self.y))
        Ensures(self.y == 20)
        Ensures(MaySet(self, 'z'))
        Ensures(MayCreate(self, 'a'))

    def some_method(self) -> None:
        Requires(MaySet(self, 'z'))
        Requires(MayCreate(self, 'a'))
        self.z = 10
        self.a = 100
        Ensures(Acc(self.z))
        Ensures(self.z == 10)
        Ensures(Acc(self.a))
        Ensures(self.a == 100)


class Normal:
    def __init__(self) -> None:
        self.x = "25"
        Ensures(Acc(self.x))
        Ensures(self.x == "25")


def main() -> None:
    c = Parent()
    Assert(c.x == "15")
    Assert(c.y == 20)
    c.z = 22

    # c.a = 22      # this would create an error
                    # because some_method has Requires(MayCreate(self, 'a'))

    c.some_method()
    Assert(c.z == 10)
    Assert(c.a == 100)
    # some_func(c)


if __name__ == "__main__":
    main()



