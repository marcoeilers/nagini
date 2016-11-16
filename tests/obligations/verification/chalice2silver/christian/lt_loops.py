"""
This test is a ported version of
``obligations/christian/lt_loops.chalice`` test from Chalice2Silver test
suite.
"""


from threading import Lock

from py2viper_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Invariant,
    Implies,
    Requires,
)
from py2viper_contracts.obligations import *
from typing import Optional


class A:

    def __init__(self) -> None:
        self.a = None       # type: Optional[Lock]
        self.b = 0          # type: int

    def m1(self) -> None:
        Requires(MustTerminate(1))
        x = 5
        while x > 0:
            Invariant(MustTerminate(x + 1))
            x -= 1

    def m2(self) -> None:
        Requires(MustTerminate(1))
        x = 5
        while x > 0:
            Invariant(MustTerminate(x))
            y = 500
            while y > 100:
                Invariant(MustTerminate(y))
                y -= 2
            x -= 1

    def d2(self) -> None:
        Requires(MustTerminate(2))

    def m3(self) -> None:
        Requires(MustTerminate(2))
        x = 5
        while x > 0:
            Invariant(MustTerminate(x))
            self.m1()
            y = 500
            while y > 100:
                Invariant(MustTerminate(y))
                self.m1()
                y -= 2
            x -= 1

    def m4(self) -> None:
        Requires(MustTerminate(2))
        x = 5
        while x > 0:
            Invariant(MustTerminate(x))
            y = 500
            while y > 100:
                Invariant(MustTerminate(y))
                #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
                self.d2()
                y -= 2
            x -= 1

    def m5(self) -> None:
        Requires(MustTerminate(1))
        x = 5
        #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
        while x > 0:
            Invariant(MustTerminate(1))
            x -= 1

    def m6(self) -> None:
        Requires(MustTerminate(1))
        x = 5
        #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
        while x > 0:
            Invariant(MustTerminate(x+1))
            pass

    def m7(self) -> None:
        Requires(Acc(self.b) and self.b > 17)
        Requires(Acc(self.a) and MustRelease(self.a, self.b))
        Ensures(Acc(self.a) and Acc(self.b))
        Ensures(MustRelease(self.a, self.b))

        while self.b > 2:
            Invariant(Acc(self.b) and MustTerminate(self.b))
            self.b -= 1

    def m8(self) -> None:
        Requires(Acc(self.b) and self.b > 17)
        Requires(Acc(self.a) and MustRelease(self.a, self.b))

        while self.b > 2:
            Invariant(Acc(self.b) and MustTerminate(self.b))
            self.b -= 1
        self.a.release()

    def m9(self) -> None:
        Requires(Acc(self.b) and self.b > 17)
        Requires(Acc(self.a) and MustRelease(self.a, self.b))

        while self.b > 2:
            Invariant(Acc(self.a) and Acc(self.b))
            Invariant(Implies(self.b > 4, MustRelease(self.a, self.b)))
            if self.b > 4:
                self.b -= 1
                if self.b == 4:
                    self.a.release()

    def m10(self) -> None:
        Requires(Acc(self.a) and MustRelease(self.a, 2))
        while True:
            Invariant(Acc(self.a) and MustRelease(self.a, 1))
            self.a.release()
            self.a.acquire()
