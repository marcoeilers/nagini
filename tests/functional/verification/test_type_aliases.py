# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Optional


class A:
    pass

class B:
    pass

C = A
MY_TYPE = List[A]
MY_TYPE2 = List[C]
MY_TYPE3 = List[B]


def m(l: MY_TYPE, l2: MY_TYPE2) -> None:
    Requires(list_pred(l) and len(l) > 0)
    Requires(list_pred(l2) and len(l) > 0)
    v1 = l[0]
    v2 = l2[0]
    assert isinstance(l, list)
    assert isinstance(v1, C)
    assert isinstance(v2, A)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(v1, B)


def m2() -> None:
    a = C()
    assert isinstance(a, A)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(a, B)
