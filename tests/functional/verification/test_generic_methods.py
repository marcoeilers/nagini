# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Generic, TypeVar, List, Tuple

T = TypeVar('T')
V = TypeVar('V', bound=int)


class Container:
    def __init__(self) -> None:
        pass


def m(v: V, lt: List[T]) -> Tuple[T, V, int]:
    Requires(Acc(list_pred(lt)) and len(lt) > 0)
    return lt[0], v, 2 + v


def client() -> None:
    cont = Container()
    t = m(True, [cont])
    assert isinstance(t[0], Container)
    assert isinstance(t[1], bool)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def m_used_twice(v: V, lt: List[T], t: T, b: bool) -> Tuple[T, V, int]:
    Requires(Acc(list_pred(lt)) and len(lt) > 0)
    if b:
        t_res = t
    else:
        t_res = lt[0]
    return t_res, v, 2 + v


def client_used_twice() -> None:
    cont = Container()
    t = m_used_twice(True, [cont], cont, True)
    assert isinstance(t[0], Container)
    assert isinstance(t[1], bool)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def m_used_twice_2(v: V, t: T, lt: List[T], b: bool) -> Tuple[T, V, int]:
    Requires(Acc(list_pred(lt)) and len(lt) > 0)
    if b:
        t_res = t
    else:
        t_res = lt[0]
    return t_res, v, 2 + v


def client_used_twice_2() -> None:
    cont = Container()
    t = m_used_twice_2(True, cont, [cont], True)
    assert isinstance(t[0], Container)
    assert isinstance(t[1], bool)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


class A(Generic[V]):
    def __init__(self, v: V) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = v

    def method(self, t: T) -> Tuple[T,V]:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        return t,self.v

    def method_2(self, t: T) -> Tuple[T,V]:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        return t,self.v


def a_client() -> None:
    a = A(True)  # type: A[bool]
    cont = Container()
    a1 = a.method(cont)
    assert isinstance(a1[1], bool)
    assert isinstance(a1[0], Container)
    a2 = a.method_2(cont)
    assert isinstance(a2[1], bool)
    assert isinstance(a2[0], Container)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


class B(Generic[V], A[V]):
    def method_2(self, t: T) -> Tuple[T,V]:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        return t,self.v