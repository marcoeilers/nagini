from abc import ABC
from typing import Generic, TypeVar
from nagini_translation.native.vf.standard.consumer import Consumer
from nagini_translation.native.vf.standard.value import Value, ValueT

class Inductive(Value, ABC):
    pass

class list(Inductive, Generic[ValueT], ABC):
    def __init__(self, head: ValueT, tail: list[ValueT]):
        pass
class cons(list, Consumer):
    def __init__(self, head: ValueT, tail: list[ValueT]):
        self.__head = head
        self.__tail = tail
    def __str__(self) -> str:
        return "cons(" + str(self.__head) + ", " + str(self.__tail) + ")"

class nil(list):
    def __str__(self) -> str:
        return "nil"

ValueT2 = TypeVar("ValueT2", bound="Value")
class Pair(Value, Consumer, Generic[ValueT, ValueT2]):
    pass
