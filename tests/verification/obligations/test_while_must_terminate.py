from py2viper_contracts.contracts import (
    Assert,
    Requires,
    Invariant,
    Implies,
)
from py2viper_contracts.io import IOExists1
from py2viper_contracts.obligations import *


def non_terminating() -> None:
    pass


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
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_not_promised)
    while True:
        pass


def test_terminate_promise_2() -> None:
    Requires(MustTerminate(1))
    while False:
        pass


def test_terminate_promise_3() -> None:
    Requires(MustTerminate(1))
    i = 0
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_not_promised)
    while i < 5:
        i += 1


def test_terminate_promise_4() -> None:
    Requires(MustTerminate(1))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        j = 0
        #:: ExpectedOutput(leak_check.failed:must_terminate.loop_not_promised)
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
