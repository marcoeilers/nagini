from py2viper_contracts.contracts import (
    Assert,
    Requires,
    Invariant,
    Implies,
)
from py2viper_contracts.io import IOExists1
from py2viper_contracts.obligations import *


# Check that MustTerminate obligation is not lost by using loop.


def non_terminating() -> None:
    pass


def test_call_non_terminating_1() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
    #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
    non_terminating()


def test_call_non_terminating_2() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
        non_terminating()


def test_call_non_terminating_3() -> None:
    Requires(MustTerminate(2))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1
        j = 0
        while j < 5:
            Invariant(MustTerminate(5 - j))
            j += 1
        #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
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
            #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
            non_terminating()


def test_call_non_terminating_5() -> None:
    Requires(MustTerminate(2))
    a = [1, 2, 3]
    i = 0
    for elem in a:
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(MustTerminate(len(a) - i))
        i += 1
    #:: OptionalOutput(leak_check.failed:must_terminate.not_taken)
    non_terminating()


# Check that measures are non-negative.


def test_measures_1() -> None:
    while True:
        #:: ExpectedOutput(invariant.not.established:assertion.false)
        Invariant(MustTerminate(-1))
        a = 2


def test_measures_2() -> None:
    while False:
        # Negative measure is ok because loop is never executed.
        Invariant(MustTerminate(-1))
        a = 2


def test_measures_3() -> None:
    i = 5
    while i > 0:
        Invariant(MustTerminate(i))
        i -= 1


def test_measures_4() -> None:
    i = 5
    while i > -1:
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(MustTerminate(i))
        i -= 1
