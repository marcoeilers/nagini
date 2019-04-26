# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import (
    Optional,
    Union,
)

class A:
    def some_int(self) -> int:
        Ensures(Result() == 5)
        return 5

class B:
    def some_int(self) -> int:
        Ensures(Result() == 7)
        return 7

class C:
    def some_val(self) -> None:
        pass

class D:
    def some_val(self) -> None:
        pass

class E:
    @Pure
    def some_int(self) -> int:
        return 5

    @Pure
    def some_val(self) -> int:
        return 8

class F:
    @Pure
    def some_int(self) -> int:
        return 7

class G:
    def some_val(self) -> str:
        return 'test'

class H:
    def some_val(self) -> int:
        return 1

def test_union_impure_methods(u: Union[A, B]) -> int:
    Ensures(Result() == 5 or Result() == 7)
    return u.some_int()

def test_union_methods(u: Union[C, D]) -> None:
    u.some_val()

def test_union_pure_functions_1(u: Union[E, F]) -> int:
    Ensures(Result() == 5 or Result() == 7)
    return u.some_int()

@Pure
def test_union_pure_functions_2(u: Union[E, F]) -> int:
    Ensures(Result() == 5 or Result() == 7)
    return u.some_int()

def test_mixing_pure_and_impure(u: Union[A, F]) -> int:
    Ensures(Result() == 5 or Result() == 7)
    return u.some_int()

def test_absence_of_name_clashes(a: Union[A, B], b: Union[C, D],
                                 c: Union[E, F]) -> None:
    a.some_int()
    b.some_val()
    c.some_int()

def test_union_mixing_return_types(u: Union[G, H]) -> Union[int, str]:
    return u.some_val()
