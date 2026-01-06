# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class A:
    def __init__(self, val: int) -> None:
        Ensures(Acc(self._field))  # type: ignore
        Ensures(self.field == val)
        self._field = val

    @property
    def field(self) -> int:
        Requires(Acc(self._field))
        return self._field

class B(A):

    def __init__(self, val: int) -> None:
        Ensures(Acc(self._field))
        Ensures(self.field == val)
        super().__init__(val)

    @Pure
    def non_zero(self) -> bool:
        Requires(Acc(self._field))
        return self.field != 0

def test1() -> None:
    b = B(5)

    assert b.non_zero()


class C(A):

    def __init__(self, val: int) -> None:
        Ensures(Acc(self._field))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(self.field == val + 1)
        super().__init__(val)

