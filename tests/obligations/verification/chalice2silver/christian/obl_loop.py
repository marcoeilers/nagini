# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/christian/obl_loop.chalice`` test from Chalice2Silver test
suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Implies,
    Invariant,
    Predicate,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock
from typing import Optional


class ObjectLock(Lock['A']):
    @Predicate
    def invariant(self) -> bool:
        return True

class A:

    def __init__(self) -> None:
        self.x = None   # type: Optional[ObjectLock]
        self.y = 0

    def m1_hide(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
        while x < 5:
            x += 1
        self.x.release()

    def m2_hide(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        while x < 5:
            Invariant(MustTerminate(10-x))
            x += 1
        self.x.release()

    def m2_transfer_rel(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        while x < 5:
            Invariant(Acc(self.x))
            Invariant(Implies(x < 5, MustRelease(self.x, 10-x)))
            x += 1
            if x >= 5:
                self.x.release()

    def m2_borrow_rel(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        while x < 5:
            Invariant(Acc(self.x))
            Invariant(MustRelease(self.x, 10-x))
            x += 1
        self.x.release()

    def nested1(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        y = 1
        while x < 5:
            Invariant(Acc(self.x) and MustRelease(self.x, 10 - x))
            x += 1
            #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
            while y < 5:
                y += 1
        self.x.release()

    def nested1_after_inner(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        y = 1
        while x < 5:
            Invariant(Acc(self.x))
            Invariant(Implies(x < 5, MustRelease(self.x, 10 - x)))
            x += 1
            #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
            while y < 5:
                y += 1
            if x == 5:
                self.x.release()

    def nested2(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        y = 1
        while x < 5:
            Invariant(Acc(self.x))
            Invariant(MustRelease(self.x, 10 - x))
            x += 1
            while y < 5:
                Invariant(MustTerminate(20 - y))
                y += 1
        self.x.release()

    def nested2_after_inner(self) -> None:
        Requires(Acc(self.x) and MustRelease(self.x, 2))
        x = 1
        y = 1
        while x < 5:
            Invariant(Acc(self.x))
            Invariant(Implies(x < 5, MustRelease(self.x, 10 - x)))
            x += 1
            while y < 5:
                Invariant(MustTerminate(20 - y))
                y += 1
            if x == 5:
                self.x.release()

    def nested3(self) -> None:
        Requires(Acc(self.x) and self.x is not None)
        Requires(WaitLevel() < Level(self.x))
        x = 1
        y = 1
        self.x.acquire()
        while x < 5:
            Invariant(Acc(self.x))
            Invariant(MustRelease(self.x, 10 - x))
            x += 1
            #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
            while y < 5:
                y += 1
        self.x.release()

    def nested4(self) -> None:
        Requires(Acc(self.x) and self.x is not None)
        Requires(WaitLevel() < Level(self.x))
        x = 1
        self.x.acquire()
        while x < 5:
            Invariant(Acc(self.x))
            Invariant(Implies(x < 5, MustRelease(self.x, 10 - x)))
            x += 1
            y = 1
            while y < 5:
                Invariant(Acc(self.x))
                Invariant(Implies(y < 5 or x < 5, MustRelease(self.x, 10 - y)))
                y += 1
                if y == 5 and x == 5:
                    self.x.release()

    def nested4_convert_reject(self) -> None:
        Requires(Acc(self.x) and self.x is not None)
        Requires(WaitLevel() < Level(self.x))
        Ensures(Acc(self.x))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(MustRelease(self.x))
        x = 1
        y = 2
        self.x.acquire()
        while x < 5:
            Invariant(y <= 5)
            Invariant(Acc(self.x))
            Invariant(MustRelease(self.x, 10 - x))
            x += 1
            while y < 5:
                Invariant(y <= 5)
                Invariant(Acc(self.x))
                Invariant(MustRelease(self.x, 10 - y))
                y += 1

    def nested4_convert_accept(self) -> None:
        Requires(Acc(self.x) and self.x is not None)
        Requires(WaitLevel() < Level(self.x))
        Ensures(Acc(self.x))
        Ensures(MustRelease(self.x, 1))
        x = 1
        y = 2
        self.x.acquire()
        while x < 5:
            Invariant(y <= 5)
            Invariant(Acc(self.x))
            Invariant(MustRelease(self.x, 10 - x))
            x += 1
            while y < 5:
                Invariant(y <= 5)
                Invariant(Acc(self.x))
                Invariant(MustRelease(self.x, 10 - y))
                y += 1