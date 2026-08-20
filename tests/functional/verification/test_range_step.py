# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def step_len_pass() -> None:
    a = range(0, 10, 2)
    assert len(a) == 5


def step_len_fail() -> None:
    a = range(0, 10, 2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(a) == 10


def step_getitem_pass() -> None:
    a = range(0, 10, 2)
    assert a[0] == 0
    assert a[2] == 4
    assert a[4] == 8


def step_getitem_fail() -> None:
    a = range(0, 10, 2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a[2] == 5


def step_with_start_pass() -> None:
    a = range(1, 10, 3)
    assert len(a) == 3
    assert a[0] == 1
    assert a[2] == 7


def step_with_start_fail() -> None:
    a = range(1, 10, 3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a[1] == 3


def step_rounding_pass() -> None:
    # range(0, 9, 2) == [0, 2, 4, 6, 8], length 5.
    a = range(0, 9, 2)
    assert len(a) == 5
    assert a[4] == 8


def step_empty_pass() -> None:
    a = range(10, 0, 2)
    assert len(a) == 0


def step_nonpositive_fail() -> None:
    # Only a positive step is supported; the precondition step >= 1 fails.
    #:: ExpectedOutput(application.precondition:assertion.false)
    a = range(0, 10, 0)
