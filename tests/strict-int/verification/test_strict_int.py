"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from nagini_contracts.contracts import *


def takes_int(x: int) -> None:
    Requires(True)


def test_int_arg_accepted() -> None:
    takes_int(42)


def test_bool_arg_rejected() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    takes_int(True)


def returns_bool_as_int() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    return True


def test_forall_int_verifies() -> None:
    Assert(Forall(int, lambda k: (k is not True and k is not False, [])))
