# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Clazz:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        Ensures(Acc(self.y))
        self.x = 5  # type: int
        self.y = 3  # type: int

    def m1(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Rd(self.x))
        Ensures(Acc(self.y) and Rd(self.x) and self.y == self.x + 1)
        self.y = self.x + 1

    def m2(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x) and self.x == 5)
        Ensures(Acc(self.y) and Acc(self.x) and self.x == 5 and self.y == self.x + 1)
        self.y = 1
        self.m1()
        Assert(self.y == 6 and self.x == 5)
