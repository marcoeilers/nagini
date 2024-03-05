# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Any


@Complex
class Parent:
    def __init__(self) -> None:
        self.x = 15
        Ensures(Acc(self.x))
        # Ensures(self.x == 15)
        # Ensures(MayCreate(self, 'y'))
        # Ensures(MayCreate(self, 'z'))



# @Complex
# class Child(Parent):
#     def __init__(self) -> None:
#         super().__init__()
#         self.y = "20"
#         Ensures(Acc(self.x))
#         Ensures(self.x == "15")
#         Ensures(Acc(self.y))
#         Ensures(self.y == "20")
#         Ensures(MayCreate(self, 'z'))


class Normal:
    def __init__(self) -> None:
        self.x = 25
        Ensures(Acc(self.x))
        Ensures(self.x == 25)


def main() -> None:
    # c = Child()
    # Assert(c.x == 15)
    # p = Parent()
    # Assert(p.x == "15")
    # local_var = p.x
    # p.x = "5"
    # Assert(p.x == "5")
    pass


if __name__ == "__main__":
    main()



