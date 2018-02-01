# chaliceSuite/permission-model/basic.chalice

from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread


class Cell:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        self.x = 0  # type: int

    # dispose a read permission to x
    def dispose_rd(self) -> None:
        Requires(Rd(self.x))
        Ensures(True)

    # return read permission
    def void(self) -> None:
        Requires(Rd(self.x))
        Ensures(Rd(self.x))

    # multiple calls to method that destroys rd(x)
    def a1(self) -> None:
        Requires(Rd(self.x))
        Ensures(True)
        self.dispose_rd()
        self.dispose_rd()

    # call to method that destroys rd(x) really removes permission
    def a2(self) -> None:
        Requires(Rd(self.x))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Rd(self.x))
        self.dispose_rd()

    # forking and method calls of dispose_rd
    def a3(self) -> None:
        Requires(Rd(self.x))
        Ensures(True)
        t1 = Thread(None, self.dispose_rd, args=())
        t1.start(self.dispose_rd)
        self.dispose_rd()
        t2 = Thread(None, self.dispose_rd, args=())
        t2.start(self.dispose_rd)
        self.dispose_rd()

    # forking and method calls of dispose_rd
    def a4(self) -> None:
        Requires(Rd(self.x))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Rd(self.x))
        t1 = Thread(None, self.dispose_rd, args=())
        t1.start(self.dispose_rd)

    # We should retain some permission
    def a6(self) -> None:
        Requires(Rd(self.x))
        Ensures(Acc(self.x, ARP(1)))
        self.dispose_rd()

    # finite loop of method calls, preserving rd(x)
    def a11(self) -> None:
        Requires(Rd(self.x))
        Ensures(Rd(self.x))
        i = 0  # type: int
        while i < 1000:
            Invariant(Rd(self.x))
            self.void()
            i += 1

    # calling dispose_rd in a loop
    def a14(self) -> None:
        Requires(Rd(self.x))
        Ensures(True)
        self.dispose_rd()
        i = 0  # type: int
        while i < 1000:
            Invariant(Wildcard(self.x))
            self.dispose_rd()
            i += 1

    # return unknown permission
    def a15(self) -> None:
        Requires(Rd(self.x))
        Ensures(Wildcard(self.x))
        self.dispose_rd()

    # rd in loop invariant
    def a16(self) -> None:
        Requires(Rd(self.x))
        Ensures(Wildcard(self.x))
        self.dispose_rd()
        i = 0  # type: int
        while i < 1000:
            Invariant(Rd(self.x))
            self.void()
            i += 1

    # rd in method contracts
    def a17(self) -> None:
        Requires(Rd(self.x))
        self.dispose_rd()
        self.a17()

    # multiple rd in method contracts
    def a18(self) -> None:
        Requires(Rd(self.x))
        Ensures(Rd(self.x))
        self.a18a()
        self.a18a()
        self.a18b()
        self.a18b()

    def a18a(self) -> None:
        Requires(Acc(self.x, 2*ARP()))
        Ensures(Acc(self.x, ARP()+ARP()))
        pass

    def a18b(self) -> None:
        Requires(Acc(self.x, ARP()+ARP()))
        Ensures(Acc(self.x, 2*ARP()))
        pass
