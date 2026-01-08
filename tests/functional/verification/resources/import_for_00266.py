# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from typing import Generic, TypeVar
from nagini_contracts.contracts import *

TDVal = TypeVar('TDVal')


class foo(Generic[TDVal]):

    def __init__(self, val: TDVal) -> None:
        Ensures(Acc(self.value) and self.value is val)
        self.value: TDVal = val

    @staticmethod
    def bar() -> 'foo[bool]':
        Ensures(Acc(Result().value))
        Ensures(Result().value)
        return foo[bool](True)