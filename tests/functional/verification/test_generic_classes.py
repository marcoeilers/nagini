# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import TypeVar, Generic, List, Tuple

T = TypeVar('T')
V = TypeVar('V', bound=int)


class Super(Generic[T, V]):
    def __init__(self, t: T, v: V) -> None:
        Ensures(Acc(self.t) and self.t is t)  # type: ignore
        Ensures(Acc(self.v) and self.v is v)  # type: ignore
        self.t = t
        self.v = v

    def get_t(self) -> T:
        Requires(Acc(self.t))
        Ensures(Acc(self.t))
        return self.t

    def get_v(self) -> V:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        return self.v

    def use_upper_bound(self) -> int:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        return 15 + self.v


class A(Generic[T], Super[T, bool]):

    def use_int(self) -> int:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        a = self.get_v()
        b = a + 23
        return b

    def create_list(self) -> List[T]:
        Ensures(Acc(list_pred(Result())))
        result = []  # type: List[T]
        return result

    def assign_true(self) -> None:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        self.v = True

    def use_bool_field(self, l: List[bool]) -> None:
        Requires(Acc(list_pred(l)))
        Requires(Acc(self.v))
        l.append(self.v)
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert False


def constructor_client() -> None:
    a = Super('asd', True)  # type: Super[str, bool]
    b = A(12, False)  # type: A[int]
    assert isinstance(a.get_t(), str)
    assert isinstance(a.get_v(), bool)
    assert isinstance(b.get_v(), bool)
    assert isinstance(b.get_t(), int)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(b.get_t(), bool)


def list_client(su: A[bytes]) -> None:
    if su is not None:
        l = su.create_list()
        if len(l):
            b = l[0]
            assert isinstance(b, bytes)
            #:: ExpectedOutput(assert.failed:assertion.false)
            assert False


def client(su_str_int: Super[str, int]) -> None:
    Requires(Acc(su_str_int.t) and Acc(su_str_int.v))
    t = su_str_int.get_t()
    assert isinstance(t, str)
    v = su_str_int.get_v()
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(v, bool)


def client_subclass(a_tuple: A[Tuple[str, str]]) -> None:
    Requires(Acc(a_tuple.t) and Acc(a_tuple.v))
    t = a_tuple.get_t()
    t_first = t[0]
    assert isinstance(t_first, str)
    v = a_tuple.get_v()
    assert isinstance(v, bool)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


class TestClass:
    def m(self) -> int:
        Ensures(Result() == 2)
        return 2


W = TypeVar('W', bound=TestClass)


class TestClassGeneric(Generic[W]):
    def __init__(self, w: W) -> None:
        Ensures(Acc(self.val))  # type: ignore
        self.val = w.m()