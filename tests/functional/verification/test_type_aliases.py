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


def m(l: MY_TYPE) -> None:
    assert isinstance(l, MY_TYPE2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(l, MY_TYPE3)


def m2() -> None:
    a = C()
    assert isinstance(a, A)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(a, B)