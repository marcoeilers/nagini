# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    Assert,
    Requires,
    Invariant,
    Implies,
    list_pred,
    Previous,
)
from nagini_contracts.io_contracts import IOExists1
from nagini_contracts.obligations import *
from typing import List


def non_terminating() -> None:
    pass


# Check that loop does not “eat” termination obligation.


def test_call_non_terminating_5() -> None:
    Requires(MustTerminate(2))
    a = [1, 2, 3]
    for elem in a:
        Invariant(MustTerminate(len(a) - len(Previous(elem))))
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    non_terminating()


# Check that measures are non-negative.


def test_measures_1(a: List[int]) -> None:
    Requires(Acc(list_pred(a)))
    for i in a:
        #:: ExpectedOutput(invariant.not.established:obligation_measure.non_positive)
        Invariant(MustTerminate(-1))


def test_measures_2() -> None:
    a = []  # type: List[int]
    for i in a:
        # Negative measure is ok because loop is never executed.
        Invariant(MustTerminate(-1))


def test_measures_3(a: List[int]) -> None:
    Requires(Acc(list_pred(a)))
    for i in a:
        Invariant(MustTerminate(len(a) - len(Previous(i))))


def test_measures_4(a: List[int]) -> None:
    Requires(Acc(list_pred(a)))
    Requires(len(a) > 1)
    for i in a:
        #:: ExpectedOutput(invariant.not.preserved:obligation_measure.non_positive)
        Invariant(MustTerminate(len(a) - len(Previous(i)) - 1))


# Check that loop promises to terminate.


def test_terminate_promise_1(a: List[int]) -> None:
    Requires(MustTerminate(2))
    Requires(Acc(list_pred(a)))
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    for i in a:
        pass


def test_terminate_promise_2() -> None:
    Requires(MustTerminate(2))
    a = []      # type: List[int]
    for i in a:
        pass


def test_terminate_promise_4(a: List[int], b: List[int]) -> None:
    Requires(MustTerminate(2))
    Requires(Acc(list_pred(a)))
    Requires(Acc(list_pred(b)))
    for i in a:
        Invariant(MustTerminate(len(a) - len(Previous(i))))
        Invariant(Acc(list_pred(b)))
        #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
        for j in b:
            pass


# Check that loop keeps a promise to terminate.


def test_terminate_keep_promise_1() -> None:
    a = [1, 2, 3]
    for i in a:
        Invariant(MustTerminate(len(a) - len(Previous(i))))
        #:: ExpectedOutput(call.precondition:insufficient.permission)
        a.append(4)


# Check that loop does not generate obligations.


def test_generation_1(a: List[int]) -> None:
    Requires(Acc(list_pred(a)))
    for i in a:
        Invariant(MustTerminate(len(a) - len(Previous(i))))
    non_terminating()


# Check that exhale always succeeds.


def test_exhale_1(a: List[int]) -> None:
    Requires(Acc(list_pred(a)))
    for i in a:
        Invariant(MustTerminate(len(a) - len(Previous(i))))
        Invariant(MustTerminate(1 + len(a) - len(Previous(i))))
