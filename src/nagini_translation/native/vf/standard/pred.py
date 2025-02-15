from typing import Type, Tuple, TypeVar, Generic
from nagini_translation.native.vf.standard.value import Value

_T = TypeVar("T", bound=Tuple[Value, ...])


class Pred(Generic[_T]):
    def __init__(self, name: str):
        self.__name = name
    def getName(self) -> str:
        return self.__name