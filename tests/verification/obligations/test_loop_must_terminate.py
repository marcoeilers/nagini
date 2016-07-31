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
