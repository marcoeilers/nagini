from py2viper_contracts.contracts import *
from typing import TypeVar, Generic, Tuple

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
        return self.t

    def get_v(self) -> V:
        Requires(Acc(self.v))
        return self.v


class A(Generic[T], Super[T, int]):

    def use_int(self) -> int:
        Requires(Acc(self.v))
        a = self.get_v()
        b = a + 23
        return b


def client(su_str_int: Super[str, int]) -> None:
    Requires(Acc(su_str_int.t) and Acc(su_str_int.v))
    t = su_str_int.get_t()
    assert isinstance(t, str)
    v = su_str_int.get_v()
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(v, bool)