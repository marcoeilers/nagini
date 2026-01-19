# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class A:

    @property
    def seg(self) -> PSeq[int]:
        return PSeq(1,2,3)

class B(A):
    def test_is(self) -> None:
        Ensures(self.seg is Old(self.seg))
        pass


class A2:
    def __init__(self) -> None:
        self.urgh = 5


class B2(A2):
    def test_is(self) -> None:
        Ensures(Acc(self.urgh))
        Ensures(self.urgh is self.urgh)
        Assume(False)