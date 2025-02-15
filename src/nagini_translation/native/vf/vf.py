from nagini_translation.native.vf.standard.expr import *
from nagini_translation.native.vf.standard.fact import *
from nagini_translation.native.vf.standard.inductive import *
from nagini_translation.native.vf.standard.literal import *
from nagini_translation.native.vf.standard.name import *
from nagini_translation.native.vf.standard.value import *
from nagini_translation.native.vf.standard.valueloc import *

_ValueT2 = TypeVar("_ValueT2", bound="Value")
_ValueT = TypeVar("_ValueT", bound="Value")


class Pair(Inductive, Generic[ValueT, ValueT2]):
    def __init__(self, first: ValueT, second: ValueT2):
        self.__first = ValueLocation[ValueT](first)
        self.__second = ValueLocation[ValueT](second)

class List(Inductive, Generic[ValueT], ABC):

    def __init__(self, head: ValueT, tail: list[ValueT]):
        pass


class Cons(List[ValueT]):
    def __init__(self, head: ValueT, tail: list[ValueT]):
        self.__head = head
        self.__tail = tail

    def __str__(self) -> str:
        return "cons(" + str(self.__head) + ", " + str(self.__tail) + ")"


class Nil(List):
    def __str__(self) -> str:
        return "nil"
