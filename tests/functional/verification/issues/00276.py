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

def test_produce_seq() -> A[PSeq[int]]:
    Ensures(Acc(Result()._value))
    Ensures(isinstance(Result().value, PSeq))
    Ensures(len(Result().value) == 3)
    return A[PSeq[int]](PSeq(1,2,3))


class A2(Generic[T]):

    def __init__(self, val: Optional[T] = None) -> None:
        Ensures(Acc(self._value) and self._value is val) # type: ignore
        self._value = val

    @Pure
    def value(self) -> Optional[T]:
        Requires(Acc(self._value))
        return self._value

def test_produce_seq2() -> A2[PSeq[int]]:
    Ensures(Acc(Result()._value))
    Ensures(isinstance(Result().value(), PSeq))
    Ensures(len(Result().value()) == 3)
    return A2[PSeq[int]](PSeq(1,2,3))