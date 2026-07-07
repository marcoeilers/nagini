# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Ensures, list_pred
from typing import List


def filter_member_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    Requires(src[0] > 5)
    res = [x for x in src if x > 5]  # type: List[int]
    # An element satisfying the filter is contained in the result.
    assert src[0] in res


def filter_member_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    # Without knowing src[0] > 5, membership cannot be established.
    res = [x for x in src if x > 5]  # type: List[int]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert src[0] in res


def filter_mapped_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    Requires(src[0] > 5)
    res = [x + 1 for x in src if x > 5]  # type: List[int]
    assert (src[0] + 1) in res


def filter_mapped_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    Requires(src[0] > 5)
    res = [x + 1 for x in src if x > 5]  # type: List[int]
    # Only the mapped value is guaranteed present.
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert src[0] in res


def filter_length_bound_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    res = [x for x in src if x > 5]  # type: List[int]
    assert len(res) <= len(src)


def filter_length_exact_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    res = [x for x in src if x > 5]  # type: List[int]
    # The exact length is not guaranteed for a filtered comprehension.
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(res) == len(src)
