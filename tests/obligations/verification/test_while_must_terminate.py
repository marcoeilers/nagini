# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Assert,
    Requires,
    Invariant,
    Implies,
)
from nagini_contracts.io_contracts import IOExists1
from nagini_contracts.obligations import *


def non_terminating() -> None:
    pass


def non_terminating2() -> None:
    Requires(Implies(False, MustTerminate(0)))


# Check that loop does not “eat” termination obligation.


def test_call_non_terminating_1() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    non_terminating()


def test_call_non_terminating_2() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
        non_terminating()


def test_call_non_terminating_3() -> None:
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
        non_terminating()


def test_call_non_terminating_4() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        j = 0
        while j < 5:
            Invariant(MustTerminate(5 - j))
            j += 1
        #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
        non_terminating()


def test_call_non_terminating_5() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        j = 0
        while j < 5:
            Invariant(MustTerminate(5 - j))
            j += 1
            #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
            non_terminating()


# Check that measures are non-negative.


def test_measures_1() -> None:
    while True:
        #:: ExpectedOutput(invariant.not.established:obligation_measure.non_positive)
        Invariant(MustTerminate(-1))


def test_measures_2() -> None:
    while False:
        # Negative measure is ok because loop is never executed.
        Invariant(MustTerminate(-1))


def test_measures_3() -> None:
    i = 5
    while i > 0:
        Invariant(MustTerminate(i))
        i -= 1


def test_measures_4() -> None:
    i = 5
    while i > -1:
        #:: ExpectedOutput(invariant.not.preserved:obligation_measure.non_positive)
        Invariant(MustTerminate(i))
        i -= 1


# Check that loop promises to terminate.


def test_terminate_promise_1() -> None:
    Requires(MustTerminate(1))
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while True:
        pass


def test_terminate_promise_2() -> None:
    Requires(MustTerminate(1))
    while False:
        pass


def test_terminate_promise_3() -> None:
    Requires(MustTerminate(1))
    i = 0
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < 5:
        i += 1


def test_terminate_promise_4() -> None:
    Requires(MustTerminate(1))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        j = 0
        #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
        while j < 5:
            j += 1


# Check that loop keeps a promise to terminate.


def test_terminate_keep_promise_1() -> None:
    i = 0
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i -= 1


def test_terminate_keep_promise_2() -> None:
    i = 0
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
    while i < 5:
        Invariant(MustTerminate(5 - i))
        j = 1


def test_terminate_keep_promise_3() -> None:
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        j = 0
        #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
        while j < 5:
            Invariant(MustTerminate(5 - j))
            j -= 1


def test_terminate_keep_promise_4() -> None:
    b = True
    while b:
        Invariant(Implies(b, MustTerminate(1)))
        Invariant(Implies(not b, MustTerminate(1)))
        b = False


# Check that loop does not generate obligations.


def test_generation_1() -> None:
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
    non_terminating()


def test_generation_2() -> None:
    b = True
    while b:
        Invariant(Implies(not b, MustTerminate(1)))
        b = False
    while True:
        pass


# Check that loop does not eat obligations.


def test_eating_1() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    non_terminating2()


# Check that exhale always succeeds.


def test_exhale_1() -> None:
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        Invariant(MustTerminate(6 - i))
        i += 1


def test_exhale_2() -> None:
    i = 0
    while i < 5:
        Invariant(Implies(i > 0, MustTerminate(5 - i)))
        Invariant(Implies(i > 0, MustTerminate(6 - i)))
        i += 1


# Check with non-boolean guards.


def test_non_boolean_guards() -> None:
    i = 5
    while i:
        Invariant(MustTerminate(i) if i + 1 else True)
        Invariant(i >= 0)
        i -= 1
