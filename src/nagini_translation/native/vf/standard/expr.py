from abc import ABC
from nagini_translation.native.vf.standard.value import Value
from typing import Generic
from typing import TypeVar

ValueT = TypeVar("ValueT", bound="Value")
class Expr(ABC, Generic[ValueT]):
    # any expression must return a value in the end...
    pass

class ImmediateLiteral(Expr[ValueT]):
    def __init__(self, value: ValueT):
        self.__value = value

    #def getValue(self) -> ValueT:
    #    return self.__value
