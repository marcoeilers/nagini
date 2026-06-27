# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Ensures, list_pred
from typing import List, Dict


def dict_comp_key_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    d = {x: x + 1 for x in src}  # type: Dict[int, int]
    # Accessing src[0] triggers the forward-direction key/value fact.
    assert src[0] in d


def dict_comp_key_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    d = {x: x + 1 for x in src}  # type: Dict[int, int]
    # An unrelated key is not guaranteed to be present.
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 12345 in d


def dict_comp_value_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    d = {x: x + 1 for x in src}  # type: Dict[int, int]
    assert d[src[0]] == src[0] + 1


def dict_comp_value_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    d = {x: x + 1 for x in src}  # type: Dict[int, int]
    # The value is the mapped x + 1, not x.
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert d[src[0]] == src[0]


def dict_comp_missing_key_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    d = {x: x + 1 for x in src}  # type: Dict[int, int]
    # Looking up a key that is not known to be present fails the precondition
    # of __getitem__.
    #:: ExpectedOutput(application.precondition:assertion.false)
    y = d[12345]


def dict_comp_filter_pass(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    Requires(src[0] > 5)
    d = {x: x for x in src if x > 5}  # type: Dict[int, int]
    assert src[0] in d
    assert d[src[0]] == src[0]


def dict_comp_filter_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    # Without knowing src[0] > 5, presence of the key cannot be established.
    d = {x: x for x in src if x > 5}  # type: Dict[int, int]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert src[0] in d


def dict_comp_no_reverse_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    d = {x: x + 1 for x in src}  # type: Dict[int, int]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(d) == len(src)
