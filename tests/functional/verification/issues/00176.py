# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Grandparent:
    def __init__(sef) -> None:
        sef.x = 1
        Ensures(Acc(sef.x))
        Ensures(sef.x == 1)


class Parent(Grandparent):
    def __init__(seelf) -> None:
        super().__init__()
        Ensures(Acc(seelf.x))
        Ensures(seelf.x == 1)


class Child(Parent):
    def __init__(self) -> None:
        super().__init__()
        Ensures(Acc(self.x))
        Ensures(self.x == 1)


def main() -> None:
    c = Child()
    Assert(c.x == 1)


if __name__ == "__main__":
    main()
