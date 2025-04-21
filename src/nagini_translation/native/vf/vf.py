from nagini_translation.native.vf.standard.expr import *
from nagini_translation.native.vf.standard.fact import *
from nagini_translation.native.vf.standard.inductive import *
from nagini_translation.native.vf.standard.literal import *
from nagini_translation.native.vf.standard.value import *

_ValueT2 = TypeVar("_ValueT2", bound="Value")
_ValueT = TypeVar("_ValueT", bound="Value")


class Pair(Inductive, Generic[_ValueT, _ValueT2]):
    def __init__(self, first: Expr[_ValueT], second: Expr[_ValueT2]):
        # one could be a namedefexpr and the other a nameuseexpr
        self.first = first
        self.second = second

    def __str__(self) -> str:
        return "pair(" + str(self.first) + ", " + str(self.second) + ")"


class List(Inductive, Generic[_ValueT], ABC):
    @staticmethod
    def from_list(lst: list[Expr[_ValueT]]) -> "List[_ValueT]":
        if len(lst) == 0:
            return Nil()
        else:
            return Cons(lst[0], List.from_list(lst[1:]))


class Cons(List[_ValueT]):
    def __init__(self, head: _ValueT, tail: list[_ValueT]):
        self.head = (head)
        self.tail = (tail)

    def __str__(self) -> str:
        return "cons(" + str(self.head) + ", " + str(self.tail) + ")"


class Nil(List):
    def __str__(self) -> str:
        return "nil"


class Option(Inductive, Generic[_ValueT], ABC):
    pass


class Some(Option[_ValueT]):
    def __init__(self, value: _ValueT):
        self.value = value

    def __str__(self) -> str:
        return "some(" + str(self.value) + ")"


class None_(Option):
    def __str__(self) -> str:
        return "none"
