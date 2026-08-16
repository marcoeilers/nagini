"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from nagini_contracts.contracts import *
from typing import List, Optional, Tuple


def opt_list_pred_no_invariant(xs: Optional[List[int]]) -> int:
    # The list invariant only applies to actual list types; an Optional argument
    # (type_args [None, list]) crashed the translator here.
    Requires(Implies(xs is not None, Acc(list_pred(xs))))
    Ensures(Result() >= 0)
    if xs is None:
        return 0
    return len(xs)


def takes_int(x: int) -> None:
    Requires(True)


def test_int_arg_accepted() -> None:
    takes_int(42)


def test_bool_arg_rejected() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    takes_int(True)


#:: ExpectedOutput(postcondition.violated:assertion.false)
def returns_bool_as_int() -> int:
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


def reads_tuple_int_param(t: Tuple[int, int]) -> None:
    takes_int(t[0])
    takes_int(t[1])


def reads_single_int_tuple(t: Tuple[int]) -> None:
    takes_int(t[0])


def reads_homogeneous_tuple(t: Tuple[int, ...]) -> None:
    Requires(len(t) > 0)
    takes_int(t[0])


def reads_mixed_tuple(t: Tuple[int, str]) -> None:
    # Only the int slot can be passed to takes_int.
    takes_int(t[0])


def tuple_literal_strict() -> None:
    t = (1, 2, 3)
    takes_int(t[0])
    takes_int(t[2])


def unpacks_tuple_int(t: Tuple[int, int]) -> None:
    a, b = t
    takes_int(a)
    takes_int(b)


def _make_int_pair() -> Tuple[int, int]:
    return (1, 2)


def returns_tuple_int_used() -> None:
    t = _make_int_pair()
    takes_int(t[0])


def reads_bool_tuple_rejected(t: Tuple[bool, bool]) -> None:
    # Tuple[bool, bool] elements must NOT be promoted to strict int.
    #:: ExpectedOutput(call.precondition:assertion.false)
    takes_int(t[0])


def reads_bool_variadic_tuple_rejected(t: Tuple[bool, ...]) -> None:
    Requires(len(t) > 0)
    #:: ExpectedOutput(call.precondition:assertion.false)
    takes_int(t[0])
