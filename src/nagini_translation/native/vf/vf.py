from nagini_translation.native.vf.standard.expr import *
from nagini_translation.native.vf.standard.fact import *
from nagini_translation.native.vf.standard.inductive import *
from nagini_translation.native.vf.standard.literal import *
from nagini_translation.native.vf.standard.value import *

_ValueT2 = TypeVar("_ValueT2", bound="Value")
_ValueT = TypeVar("_ValueT", bound="Value")


class Pair(Inductive, Generic[_ValueT, _ValueT2]):
    def __init__(self, first: _ValueT, second: _ValueT2):
        self.__first = ValueLocation[_ValueT](first)
        self.__second = ValueLocation[_ValueT](second)

class List(Inductive, Generic[_ValueT], ABC):
    @staticmethod
    def from_list(lst: list[_ValueT]) -> "List"[_ValueT]:
        if len(lst) == 0:
            return Nil()
        else:
            return Cons(lst[0], List.from_list(lst[1:]))


class Cons(List[_ValueT]):
    def __init__(self, head: _ValueT, tail: list[_ValueT]):
        self.__head = head
        self.__tail = tail

    def __str__(self) -> str:
        return "cons(" + str(self.__head) + ", " + str(self.__tail) + ")"


class Nil(List):
    def __str__(self) -> str:
        return "nil"
