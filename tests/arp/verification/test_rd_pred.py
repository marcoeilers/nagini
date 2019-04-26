# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Clazz:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        Ensures(Acc(self.y))
        self.x = 5  # type: int
        self.y = 3  # type: int

    @Predicate
    def pred(self) -> bool:
        return Rd(self.x)

    def m1(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and self.pred())
        Ensures(Acc(self.y) and self.pred() and Unfolding(self.pred(), self.y == self.x + 1))
        Unfold(self.pred())
        self.y = self.x + 1
        Assert(Acc(self.x, RD_PRED))
        Fold(self.pred())

    def m1_1(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and self.pred())
        Ensures(Acc(self.y) and Acc(self.x, RD_PRED) and self.y == self.x + 1)
        Unfold(self.pred())
        self.y = self.x + 1

    def m1_2(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and self.pred())
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Acc(self.y) and Acc(self.x, 2*RD_PRED) and self.y == self.x + 1)
        Unfold(self.pred())
        self.y = self.x + 1

    def m1_3(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and self.pred())
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Acc(self.y) and Acc(self.x, RD_PRED + ARP(1)) and self.y == self.x + 1)
        Unfold(self.pred())
        self.y = self.x + 1

    def m2(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x) and self.x == 5)
        Ensures(Acc(self.y) and Acc(self.x) and self.x == 5 and self.y == self.x + 1)
        self.y = 1
        Fold(self.pred())
        self.m1()
        Unfold(self.pred())
        Assert(self.y == 6 and self.x == 5)
        self.y = 1
        Fold(self.pred())
        self.m1_1()
        Assert(self.y == 6 and self.x == 5)

