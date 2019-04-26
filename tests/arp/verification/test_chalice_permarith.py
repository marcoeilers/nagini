# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# chaliceSuite/permission-model/permission_arithmetic.chalice

from nagini_contracts.contracts import *


class Cell:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        Ensures(Acc(self.i))
        Ensures(Acc(self.y))
        Ensures(Acc(self.f))
        Ensures(Acc(self.g))
        self.x = 0  # type: int
        self.i = 0  # type: int
        self.y = Cell()  # type: Cell
        self.f = 0  # type: int
        self.g = 0  # type: int

    @Predicate
    def valid(self) -> bool:
        return Rd(self.x)

    def a1(self, n: int) -> None:
        Requires(Acc(self.x, 2/100) and Acc(self.x, 1/100) and Acc(self.x, 3/100) and Acc(self.x, 1/100 - ARP(7-5) + ARP(3)) and Rd(self.x) and Rd(self.y))
        Ensures(Acc(self.x, 1 - 97/100))

    def a2(self, n: int) -> None:
        Requires(Acc(self.x, 1/100 - ARP(1) - 2/100))
        Assert(False)  # this should verify, as the precondition contains an invalid permission

    def a3(self, n: int) -> None:
        #:: ExpectedOutput(silicon)(assert.failed:negative.permission)|ExpectedOutput(carbon)(assert.failed:insufficient.permission)
        Assert(Acc(self.x, 1/100 - ARP(1) - 2/100))  # ERROR: invalid (negative) permission

    def a4(self, n: int) -> None:
        Requires(n > 0)
        Requires(Acc(self.x, ARP(n)))

    def a5(self, n: int) -> None:
        Requires(n > 2)
        Requires(Acc(self.x, ARP(n) - ARP(2)))

    def a18(self) -> None:
        Requires(Acc(self.x, ARP() + ARP() - ARP() + 10/100 - ARP(5+5)))
        Ensures(Rd(self.x))
