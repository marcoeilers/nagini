from nagini_contracts.contracts import *
from typing import Union

class A:
    def some_int(self) -> int:
        Ensures(Result() == 5)
        return 5

class B:
    def some_int(self) -> int:
        Ensures(Result() == 7)
        return 7

class C:
    def some_none(self) -> None:
        pass

class D:
    def some_none(self) -> None:
        pass

class E:
    @Pure
    def some_int(self) -> int:
        return 5

class F:
    @Pure
    def some_int(self) -> int:
        return 7

def test_union_impure_methods(u: Union[A, B]) -> int:
    Ensures(Result() == 5 or Result() == 7)
    return u.some_int()

def test_union_methods(u: Union[C, D]) -> None:
    u.some_none()

def test_union_pure_functions(u: Union[E, F]) -> int:
    Ensures(Result() == 5 or Result() == 7)
    return u.some_int()

def test_absence_of_name_clashes(a: Union[A, B], b: Union[C, D],
                                 c: Union[E, F]) -> None:
    a.some_int()
    b.some_none()
    c.some_int()
