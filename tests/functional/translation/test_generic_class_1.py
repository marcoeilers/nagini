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


def constructor_client() -> None:
    #:: ExpectedOutput(invalid.program:generic.constructor.without.type)
    Super('asd', True)
