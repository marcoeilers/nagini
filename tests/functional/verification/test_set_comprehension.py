# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Ensures, list_pred
from typing import List, Set


def set_comp_member_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    s = {x for x in src}  # type: Set[int]
    # Accessing src[0] triggers the forward-direction membership fact.
    assert src[0] in s


def set_comp_member_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    s = {x for x in src}  # type: Set[int]
    # Nothing guarantees that an unrelated value is in the set.
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 12345 in s


def set_comp_mapped_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    s = {x + 1 for x in src}  # type: Set[int]
    assert (src[0] + 1) in s


def set_comp_mapped_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    s = {x + 1 for x in src}  # type: Set[int]
    # Only the mapped value src[0] + 1 is guaranteed to be present, not src[0].
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert src[0] in s


def set_comp_filter_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    Requires(src[0] > 5)
    s = {x for x in src if x > 5}  # type: Set[int]
    assert src[0] in s


def set_comp_filter_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    # Without knowing src[0] > 5, membership cannot be established for the
    # filtered comprehension.
    s = {x for x in src if x > 5}  # type: Set[int]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert src[0] in s


def set_comp_no_reverse_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    s = {x for x in src}  # type: Set[int]
    # We deliberately do not guarantee the cardinality of the result, so this
    # cannot be proven.
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(s) == len(src)
