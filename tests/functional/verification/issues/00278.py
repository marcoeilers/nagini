# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Generic, Optional, TypeVar

T = TypeVar('T')
class A(Generic[T]):

    def __init__(self, val: Optional[T] = None) -> None:
        Ensures(Acc(self._value) and self._value is val) # type: ignore
        self._value = val

    @property
    def value(self) -> Optional[T]:
        Requires(Acc(self._value))
        return self._value

def test_produce_seq2() -> A[PSeq[int]]:
    Ensures(Acc(Result()._value))
    Ensures(isinstance(Result().value(), PSeq))
    Ensures(len(Result().value()) == 3)
    Ensures(Forall(int, lambda i: Implies(0 <= i and i < 2, Result().value.drop(1)[i] == 1)))
    return A[PSeq[int]](PSeq(1,1,1))