# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    Assert,
    Implies,
    Invariant,
    Predicate,
    Requires,
    Ensures,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock
from typing import Optional


class ObjectLock(Lock[object]):
    @Predicate
    def invariant(self) -> bool:
        return True

# Check acquiring a lock.


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def acquire_1(l: Optional[ObjectLock]) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)|UnexpectedOutput(carbon)(call.precondition:assertion.false, 168)
    l.acquire()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def acquire_2(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()


def acquire_3(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    l.release()


def acquire_4(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    Ensures(MustRelease(l))
    l.acquire()


def acquire_5(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    Ensures(MustRelease(l, 10))
    l.acquire()


# Check releasing a lock.


def release_1(l: ObjectLock) -> None:
    Requires(MustRelease(l, 2))
    l.release()


def release_2(l: ObjectLock) -> None:
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    l.release()


def release_3(l: ObjectLock) -> None:
    Requires(l is not None)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    l.release()


# Check termination of primitives.


def terminating_1() -> None:
    Requires(MustTerminate(2))
    l = ObjectLock(object())


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def terminating_2(l: ObjectLock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    Requires(MustTerminate(2))
    l.acquire()


def terminating_3(l: ObjectLock) -> None:
    Requires(MustRelease(l, 2))
    Requires(MustTerminate(2))
    l.release()


# Check that measures are positive in methods.


def over_in_minus_one(l: ObjectLock) -> None:
    #:: Label(over_in_minus_one__MustRelease)
    Requires(MustRelease(l, -1))
    # Negative measure is equivalent to False.
    Assert(False)


def check_over_in_minus_one() -> None:
    l = ObjectLock(object())
    l.acquire()
    #:: ExpectedOutput(call.precondition:obligation_measure.non_positive)
    over_in_minus_one(l)


def over_in_minus_one_conditional(l: ObjectLock, b: bool) -> None:
    Requires(Implies(b, MustRelease(l, 1)))
    #:: Label(over_in_minus_one_conditional__MustRelease__False)
    Requires(Implies(not b, MustRelease(l, -1)))
    # Negative measure is equivalent to False.
    Assert(Implies(not b, False))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(False)


def check_over_in_minus_one_conditional_1() -> None:
    l = ObjectLock(object())
    l.acquire()
    over_in_minus_one_conditional(l, True)


def check_over_in_minus_one_conditional_2() -> None:
    l = ObjectLock(object())
    l.acquire()
    #:: ExpectedOutput(call.precondition:obligation_measure.non_positive)
    over_in_minus_one_conditional(l, False)


# Check that measures are positive in loops.


def test_measures_1() -> None:
    l = ObjectLock(object())
    l.acquire()
    while True:
        #:: ExpectedOutput(invariant.not.established:obligation_measure.non_positive)
        Invariant(MustRelease(l, -1))
        a = 2


def test_measures_2() -> None:
    l = ObjectLock(object())
    l.acquire()
    while False:
        # Negative measure is ok because loop is never executed.
        Invariant(MustRelease(l, -1))
        a = 2
    l.release()


def test_measures_3() -> None:
    l = ObjectLock(object())
    l.acquire()
    i = 5
    while i > 0:
        Invariant(MustRelease(l, i))
        i -= 1
    l.release()


def test_measures_4() -> None:
    l = ObjectLock(object())
    l.acquire()
    i = 5
    while i > -1:
        #:: ExpectedOutput(invariant.not.preserved:obligation_measure.non_positive)
        Invariant(MustRelease(l, i))
        i -= 1
    l.release()


# Check that obligation encoding is properly framed.


class A:

    def __init__(self) -> None:
        Ensures(Acc(self.steps) and self.steps == 0)
        self.steps = 0  # type: int


def test_loop_condition_framing_1() -> None:
    a = A()
    l = ObjectLock(object())
    l.acquire()
    i = 5
    while a.steps < 5:
        #:: ExpectedOutput(not.wellformed:loop_condition.not_framed_for_obligation_use)|MissingOutput(carbon)(not.wellformed:loop_condition.not_framed_for_obligation_use, 70)|UnexpectedOutput(carbon)(not.wellformed:insufficient.permission, 70)
        Invariant(MustRelease(l, i))
        Invariant(Acc(a.steps))
        Invariant(i == 5 - a.steps)
        a.steps += 1
        i -= 1
    l.release()


def test_loop_condition_framing_2() -> None:
    a = A()
    l = ObjectLock(object())
    l.acquire()
    i = 5
    while a.steps < 5:
        Invariant(Acc(a.steps))
        Invariant(MustRelease(l, i))
        Invariant(i == 5 - a.steps)
        a.steps += 1
        i -= 1
    l.release()