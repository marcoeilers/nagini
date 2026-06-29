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
    # The last source element cannot be overwritten by a later duplicate key, so
    # its value is pinned down.
    assert d[src[len(src) - 1]] == src[len(src) - 1] + 1


def dict_comp_value_fail(src: List[int]) -> None:
    Requires(list_pred(src))
    Requires(len(src) > 0)
    d = {x: x + 1 for x in src}  # type: Dict[int, int]
    # The value is the mapped x + 1, not x.
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert d[src[len(src) - 1]] == src[len(src) - 1]


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
    Requires(src[len(src) - 1] > 5)
    d = {x: x for x in src if x > 5}  # type: Dict[int, int]
    # The last element passes the filter and has no later duplicate.
    assert src[len(src) - 1] in d
    assert d[src[len(src) - 1]] == src[len(src) - 1]


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


def dict_comp_duplicate_key_last_wins_pass(src: List[int]) -> None:
    # When several source elements map to the same key, Python keeps the value
    # produced by the *last* such element. Here src[0] and src[1] share a key
    # (same value mod 2), so d maps that key to src[1] (the later one), e.g.
    # {x % 2: x for x in [2, 4]} == {0: 4} in Python.
    Requires(list_pred(src))
    Requires(len(src) == 2)
    Requires(src[0] % 2 == src[1] % 2)
    d = {x % 2: x for x in src}  # type: Dict[int, int]
    assert d[src[1] % 2] == src[1]


def dict_comp_duplicate_key_last_wins_fail(src: List[int]) -> None:
    # The earlier element's value does NOT survive a duplicate key.
    Requires(list_pred(src))
    Requires(len(src) == 2)
    Requires(src[0] % 2 == src[1] % 2)
    Requires(src[0] != src[1])
    d = {x % 2: x for x in src}  # type: Dict[int, int]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert d[src[0] % 2] == src[0]


def dict_comp_duplicate_key_sound_fail(src: List[int]) -> None:
    # Sanity check that duplicate keys with differing values do not make the
    # encoding inhale a contradiction (which would let us prove anything).
    Requires(list_pred(src))
    Requires(len(src) == 2)
    Requires(src[0] % 2 == src[1] % 2)
    Requires(src[0] != src[1])
    d = {x % 2: x for x in src}  # type: Dict[int, int]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
