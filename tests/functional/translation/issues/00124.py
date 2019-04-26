# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import (
    Optional,
    Union,
)

class A:
    def method(self) -> None:   # Method with no return value
        pass

class B:
    def method(self) -> int:    # Method with return value
        return 1

class C:
    @Pure
    def method(self) -> int:    # Method with return value (pure function)
        return 8

def test_union_mixing_return_with_no_return(u: Union[A, B]) -> None:
    u.method()

def test_union_mixing_return_with_no_return_pure(u: Union[A, C]) -> None:
    u.method()