# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Generic, List, TypeVar
from nagini_contracts.contracts import *

T = TypeVar('T')


class GenericResult(Generic[T]):
    def __init__(self, data: T):
        Ensures(Acc(self.data) and self.data is data)  # type: ignore
        self.data = data


class foo():
    def bar(self) -> GenericResult[List[int]]:
        return GenericResult[List[int]]([1, 2, 3])
