# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

# using this will generate something like
#   self_5 := self_1
#   arg_13 := self_1
#   arg_15 := self_0
# where self_0 is not found
# and should be self_1, just like the two lines above it


class Grandparent:
    def __init__(self) -> None:
        self.x = 1
        Ensures(Acc(self.x))
        Ensures(self.x == 1)


class Parent(Grandparent):
    def __init__(self) -> None:
        super().__init__()
        Ensures(Acc(self.x))
        Ensures(self.x == 1)


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



