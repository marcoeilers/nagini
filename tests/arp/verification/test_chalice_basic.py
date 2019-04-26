# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(silicon)(320)
# chaliceSuite/permission-model/basic.chalice

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from nagini_contracts.thread import Thread


class Cell:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        self.x = 0  # type: int

    # dispose a read permission to x
    def dispose_rd(self) -> None:
        Requires(Rd(self.x))
        Requires(MustTerminate(2))
        #Ensures(True)

    # return read permission
    def void(self) -> None:
        Requires(Rd(self.x))
        Requires(MustTerminate(2))
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
        #:: UnexpectedOutput(silicon)(call.precondition:insufficient.permission, 320)
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

    # multiple forks of dispose_rd
    def a7(self) -> None:
        Requires(Rd(self.x))
        Ensures(True)
        t1 = Thread(None, self.dispose_rd, args=())
        t1.start(self.dispose_rd)
        t2 = Thread(None, self.dispose_rd, args=())
        # probably due to timeout in silicon, does not always occur
        #:: UnexpectedOutput(silicon)(thread.start.failed:insufficient.permission, 320)
        t2.start(self.dispose_rd)
        t3 = Thread(None, self.dispose_rd, args=())
        # probably due to timeout in silicon, does not always occur
        #:: UnexpectedOutput(silicon)(thread.start.failed:insufficient.permission, 320)
        t3.start(self.dispose_rd)
        t4 = Thread(None, self.dispose_rd, args=())
        t4.start(self.dispose_rd)
        t5 = Thread(None, self.dispose_rd, args=())
        t5.start(self.dispose_rd)
        t6 = Thread(None, self.dispose_rd, args=())
        t6.start(self.dispose_rd)

    # joining to regain permission
    def a8(self, a: int) -> None:
        Requires(Rd(self.x))
        Ensures(Rd(self.x))
        t1 = Thread(None, self.void, args=())
        t1.start(self.void)
        t1.join(self.void)

    # joining to regain permission
    def a9(self, a: int) -> None:
        Requires(Rd(self.x))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Rd(self.x))
        t1 = Thread(None, self.dispose_rd, args=())
        t1.start(self.dispose_rd)
        t1.join(self.dispose_rd)

    # joining to regain permission
    def a10(self, a: int) -> None:
        Requires(Rd(self.x))
        Ensures(Implies(a == 3, Rd(self.x)))
        t1 = Thread(None, self.void, args=())
        t1.start(self.void)
        if 3 == a:
            t1.join(self.void)

    # finite loop of method calls, preserving rd(x)
    def a11(self) -> None:
        Requires(Rd(self.x))
        Ensures(Rd(self.x))
        i = 0  # type: int
        while i < 1000:
            Invariant(Rd(self.x))
            self.void()
            i += 1

    # forking dispose_rd in a loop
    def a12(self, a: int) -> None:
        Requires(Rd(self.x))
        Ensures(Wildcard(self.x))
        i = 0  # type: int
        while i < a:
            Invariant(Wildcard(self.x))
            # t1 = Thread(None, self.dispose_rd, args=())
            # t1.start(self.dispose_rd)
            i += 1

    # forking dispose_rd in a loop
    def a13(self, a: int) -> None:
        Requires(Rd(self.x))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Rd(self.x))
        i = 0  # type: int
        while i < a:
            Invariant(Wildcard(self.x))
            # t1 = Thread(None, self.dispose_rd, args=())
            # t1.start(self.dispose_rd)
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
