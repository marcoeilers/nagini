"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from nagini_contracts.contracts import *
from typing import List


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


def sum_int_list(lst: List[int]) -> int:
    Requires(Acc(list_pred(lst), 1 / 2))
    Ensures(Acc(list_pred(lst), 1 / 2))
    total = 0
    for x in lst:
        Invariant(Acc(list_pred(lst), 1 / 4))
        takes_int(x)
        total = total + x
    return total


def test_append_int_accepted() -> None:
    lst = [1, 2, 3]
    lst.append(4)
    assert lst[3] == 4


def append_bool_breaks_list_pred(lst: List[int]) -> None:
    # Appending a bool to a List[int] verifies (list_append only requires
    # issubtype), but the bool then poisons the element-type invariant, so
    # list_pred cannot be re-established at the postcondition.
    Requires(Acc(list_pred(lst)))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(list_pred(lst)))
    lst.append(True)


def reads_pseq_int_param(s: PSeq[int]) -> None:
    Requires(len(s) > 0)
    takes_int(s[0])


def reads_pseq_via_toseq(lst: List[int]) -> None:
    Requires(Acc(list_pred(lst)))
    Requires(len(lst) > 0)
    Ensures(Acc(list_pred(lst)))
    s = ToSeq(lst)
    takes_int(s[0])


def reads_pseq_int_literal() -> None:
    s = PSeq(1, 2, 3)
    takes_int(s[0])


def reads_pseq_bool_param_rejected(s: PSeq[bool]) -> None:
    # PSeq[bool] elements must NOT be promoted to strict int.
    Requires(len(s) > 0)
    #:: ExpectedOutput(call.precondition:assertion.false)
    takes_int(s[0])
