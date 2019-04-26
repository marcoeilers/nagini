# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/christian/lt_Call.chalice`` test from Chalice2Silver test
suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
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
        Ensures(Acc(self.a) and Acc(self.b))
        self.a = None   # type: Optional[ObjectLock]
        self.b = 0      # type: int

    def d3(self) -> None:
        Requires(MustTerminate(3))
        self.d2()

    def d2(self) -> None:
        Requires(MustTerminate(2))
        self.d1()

    def d1(self) -> None:
        Requires(MustTerminate(1))

    def dx(self) -> None:
        Requires(MustTerminate(1))
        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
        self.d2()

    def fib(self, n: int) -> int:
        Requires(MustTerminate(n))
        if n <= 1:
            return 1
        elif n == 2:
            return 2
        else:
            w = self.fib(n-1)
            v = self.fib(n-2)
            return w + v

    def quick_release(self, other: 'A') -> None:
        Requires(Acc(other.a))
        Requires(Acc(other.b))
        Requires(MustRelease(other.a, other.b))
        Requires(other.b >= 2)

        other.a.release()

    def timed_release_unbounded(self) -> None:
        x = A()
        x.a = ObjectLock(x)
        x.a.acquire()
        x.b = 15
        self.quick_release(x)

    def timed_release_unbounded_subzero(self) -> None:
        x = A()
        x.a = ObjectLock(x)
        x.a.acquire()
        x.b = -1
        #:: ExpectedOutput(call.precondition:obligation_measure.non_positive)
        self.quick_release(x)

    def timed_release_bounded_subzero(self, x: 'A') -> None:
        Requires(Acc(x.a) and Acc(x.b))
        Requires(MustRelease(x.a, x.b))
        Requires(x.b == -1)

        # Contradiction in precondition: x.b == -1 and x.b > 0
        Assert(False)

    def timed_release_bounded_nodec(self, other: 'A') -> None:
        Requires(Acc(other.a))
        Requires(Acc(other.b))
        Requires(MustRelease(other.a, other.b))

        #:: ExpectedOutput(call.precondition:assertion.false)|ExpectedOutput(carbon)(call.precondition:insufficient.permission)
        self.quick_release(other)

    def timed_release_bounded_statdec(self, other: 'A') -> None:
        Requires(Acc(other.a) and Acc(other.b))
        Requires(other.b > 5 and MustRelease(other.a,other.b+1))
        self.quick_release(other)

    def timed_release_bounded_mutdec(self, other: 'A') -> None:
        Requires(Acc(other.a) and Acc(other.b) and other.b > 2)
        Requires(MustRelease(other.a, other.b))
        other.b -= 1
        self.quick_release(other)