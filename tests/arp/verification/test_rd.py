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

    def m1_1(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x, ARP() + 1/2))
        Ensures(Acc(self.y) and Acc(self.x, ARP() + 1/2) and self.y == self.x + 1)
        self.y = self.x + 1

    def m1_2(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x, 1/2 + ARP()))
        Ensures(Acc(self.y) and Acc(self.x, 1/2 + ARP()) and self.y == self.x + 1)
        self.y = self.x + 1

    def m1_3(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x, 1/2 - ARP()))
        Ensures(Acc(self.y) and Acc(self.x, 1/2 - ARP()) and self.y == self.x + 1)
        self.y = self.x + 1

    # this method sometimes fails to verify, sometimes it works. Silicon probably runs into a timeout
    def m1_4(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x, 2 * ARP()))
        Ensures(Acc(self.y) and Acc(self.x, 2 * ARP()) and self.y == self.x + 1)
        self.y = self.x + 1

    def m1_5(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x, ARP(2) + 1/2))
        Ensures(Acc(self.y) and Acc(self.x, ARP(2) + 1/2) and self.y == self.x + 1)
        self.y = self.x + 1

    def m2(self) -> None:
        Requires(self != None)
        Requires(Acc(self.y) and Acc(self.x) and self.x == 5)
        Ensures(Acc(self.y) and Acc(self.x) and self.x == 5 and self.y == self.x + 1)
        self.y = 1
        self.m1()
        Assert(self.y == 6 and self.x == 5)
        self.y = 1
        self.m1_1()
        Assert(self.y == 6 and self.x == 5)
        self.y = 1
        self.m1_2()
        Assert(self.y == 6 and self.x == 5)
        self.y = 1
        self.m1_3()
        Assert(self.y == 6 and self.x == 5)
        self.y = 1
        #:: UnexpectedOutput(silicon)(call.precondition:insufficient.permission, 320)
        self.m1_4()
        Assert(self.y == 6 and self.x == 5)
        self.y = 1
        self.m1_5()
        Assert(self.y == 6 and self.x == 5)
