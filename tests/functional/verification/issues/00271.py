# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Generic, Optional, TypeVar
from nagini_contracts.contracts import *

T = TypeVar('T')
class WithOptional(Generic[T]):
    def __init__(self, value: Optional[T]) -> None:
        self.value = value
        Ensures(Acc(self.value) and self.value is value)

def produce_int() -> WithOptional[int]:
    Ensures(Acc(Result().value))
    Ensures(isinstance(Result().value, int))
    Ensures(Result().value == 3)
    value = 3
    return WithOptional[int](value)

def produce_seq() -> WithOptional[PSeq[int]]:
    Ensures(Acc(Result().value))
    Ensures(isinstance(Result().value, PSeq))
    Ensures(Result().value == PSeq(1,2,3))
    return WithOptional[PSeq[int]](PSeq(1,2,3))

def test_seq() -> None:
    s = produce_seq()
    Assert(s.value[0] == 1)