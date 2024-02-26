# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Complex
class Parent:
    def __init__(self) -> None:
        self.x = "15"
        Ensures(Acc(self.x))
        Ensures(self.x == "15")


class Child(Parent):
    def __init__(self) -> None:
        super().__init__()
        Ensures(Acc(self.x))
        Ensures(self.x == "15")


class Normal:
    def __init__(self) -> None:
        self.x = "25"
        Ensures(Acc(self.x))
        Ensures(self.x == "25")


def main() -> None:
    # c = Child()
    # Assert(c.x == 15)
    p = Parent()
    Assert(p.x == "15")

    n = Normal()
    Assert(n.x == "25")

    c = Child()
    Assert(c.x == "15")


if __name__ == "__main__":
    main()



