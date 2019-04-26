# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, list_pred, Invariant
from typing import List


def enumerate_success() -> None:
    a = [0, 1, 2, 3]
    b = enumerate(a)
    assert a is not b
    for b1, b2 in b:
        Invariant(b1 == b2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def enumerate_wrong_content_assertion() -> None:
    a = [1,2,3,4]
    b = enumerate(a)
    assert a is not b
    for b1, b2 in b:
        #:: ExpectedOutput(invariant.not.established:assertion.false)
        Invariant(b1 == b2)
    assert False


def enumerate_permission_fail(a: List[int]) -> None:
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    b = enumerate(a)

